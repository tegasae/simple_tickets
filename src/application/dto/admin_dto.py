from dataclasses import dataclass


@dataclass
class CreateAdminDTO:
    actor_admin_id: int
    first_name: str
    job_title: str =""
    last_name: str =""
    email: str =""
    phone: str =""
    login: str =""
    password: str =""

@dataclass
class AdminResponseDTO:
    admin_id: int
    first_name: str
    job_title: str
    last_name: str
    email: str
    phone: str
    login: str

