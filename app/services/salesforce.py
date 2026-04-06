import asyncio

import httpx
from fastapi import HTTPException, status

from app.models.oauth_session import OAuthSession


class SalesforceService:
    def __init__(self, session: OAuthSession):
        self.session = session

    def _headers(self) -> dict[str, str]:
        if not self.session.access_token or not self.session.salesforce_instance_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Salesforce session is not fully connected yet.",
            )

        return {
            "Authorization": f"Bearer {self.session.access_token}",
            "Content-Type": "application/json",
        }

    def _base_url(self) -> str:
        return f"{self.session.salesforce_instance_url}/services/data/v60.0/tooling"

    def _is_dev_session(self) -> bool:
        return self.session.salesforce_user_id == "local-dev-user"

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
    ) -> dict | list:
        url = f"{self._base_url()}{path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method,
                url,
                headers=self._headers(),
                params=params,
                json=json,
            )

        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.text,
            )

        if response.content:
            return response.json()
        return {}

    async def list_account_validation_rules(self) -> list[dict]:
        if self._is_dev_session():
            return [
                {
                    "id": "demo-rule-1",
                    "rule_name": "Account_Name_Must_Be_Long",
                    "object_name": "Account",
                    "active": True,
                },
                {
                    "id": "demo-rule-2",
                    "rule_name": "Annual_Revenue_Required",
                    "object_name": "Account",
                    "active": False,
                },
                {
                    "id": "demo-rule-3",
                    "rule_name": "Billing_Country_Required",
                    "object_name": "Account",
                    "active": True,
                },
            ]

        query = (
            "SELECT Id, ValidationName, Active, EntityDefinition.QualifiedApiName "
            "FROM ValidationRule "
            "WHERE EntityDefinition.QualifiedApiName = 'Account' "
            "ORDER BY ValidationName"
        )
        payload = await self._request("GET", "/query", params={"q": query})
        records = payload.get("records", [])
        items: list[dict] = []

        for record in records:
            items.append(
                {
                    "id": record["Id"],
                    "rule_name": record["ValidationName"],
                    "object_name": record["EntityDefinition"]["QualifiedApiName"],
                    "active": bool(record["Active"]),
                }
            )

        return items

    async def get_validation_rule_details(self, rule_id: str) -> dict:
        payload = await self._request("GET", f"/sobjects/ValidationRule/{rule_id}")
        metadata = payload.get("Metadata") or {}
        return {
            "id": payload.get("Id", rule_id),
            "validation_name": payload.get("ValidationName"),
            "full_name": payload.get("FullName"),
            "metadata": metadata,
            "active": bool(payload.get("Active", metadata.get("active", False))),
        }

    async def update_validation_rule_state(self, rule_id: str, active: bool) -> dict:
        if self._is_dev_session():
            return {
                "id": rule_id,
                "rule_name": rule_id,
                "active": active,
            }

        details = await self.get_validation_rule_details(rule_id)
        metadata = details["metadata"] or {}
        metadata["active"] = active

        payload = {
            "Metadata": metadata,
            "FullName": details["full_name"],
        }

        await self._request("PATCH", f"/sobjects/ValidationRule/{rule_id}", json=payload)

        return {
            "id": rule_id,
            "rule_name": details["validation_name"],
            "active": active,
        }

    async def deploy_validation_rule_changes(self, changes: list[dict]) -> list[dict]:
        tasks = [
            self.update_validation_rule_state(change["id"], bool(change["active"]))
            for change in changes
        ]
        return await asyncio.gather(*tasks)
