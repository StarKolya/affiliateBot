class AlreadyAppliedException(Exception):

    def __init__(self, account_id: int, job_id: int) -> None:
        self.account_id = account_id
        self.job_id = job_id
        super().__init__(f"Account {account_id} already applied for job {job_id}")
