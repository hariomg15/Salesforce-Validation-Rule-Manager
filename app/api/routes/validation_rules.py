from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_session
from app.db.session import get_db
from app.models.deployment_log import DeploymentLog
from app.models.oauth_session import OAuthSession
from app.schemas.validation_rules import ValidationRuleDeployRequest
from app.services.salesforce import SalesforceService


router = APIRouter()


@router.get("")
async def list_validation_rules(
    db: Session = Depends(get_db),
    session: OAuthSession = Depends(get_current_session),
) -> dict[str, list | dict]:
    service = SalesforceService(session)
    items = await service.list_account_validation_rules()

    return {
        "session": {
            "id": session.id,
            "status": session.status,
            "salesforce_org_id": session.salesforce_org_id,
        },
        "items": items,
    }


@router.post("/deploy")
async def deploy_validation_rules(
    payload: ValidationRuleDeployRequest,
    db: Session = Depends(get_db),
    session: OAuthSession = Depends(get_current_session),
) -> dict[str, list | int]:
    service = SalesforceService(session)
    results = await service.deploy_validation_rule_changes(
        [change.model_dump() for change in payload.changes]
    )

    for item in payload.changes:
        db.add(
            DeploymentLog(
                session_id=session.id,
                object_name="Account",
                rule_name=item.rule_name or item.id,
                previous_state="unknown",
                new_state="active" if item.active else "inactive",
                deploy_status="success",
                message="Validation rule updated through Tooling API.",
            )
        )

    db.commit()

    return {
        "updated_count": len(results),
        "items": results,
    }
