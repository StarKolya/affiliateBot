import csv
from typing import TYPE_CHECKING, Generator, List

if TYPE_CHECKING:
    from bot.models.application import JobApplication

_CSV_FIELDS = ["id", "account", "telegram_id", "job", "status", "applied_at"]


def iter_application_rows(applications: List["JobApplication"]) -> Generator[dict, None, None]:
    for app in applications:
        yield {
            "id": app.id,
            "account": app.account.name,
            "telegram_id": str(app.account.telegram_id),
            "job": app.job_posting.title,
            "status": app.status.name,
            "applied_at": app.created_at.strftime("%Y-%m-%d %H:%M"),
        }


def export_applications_csv(applications: List["JobApplication"]) -> str:
    path = f"/tmp/applications_export_{len(applications)}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_FIELDS)
        writer.writeheader()
        for row in iter_application_rows(applications):
            writer.writerow(row)
    return path
