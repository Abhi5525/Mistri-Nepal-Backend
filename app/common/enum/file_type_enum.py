from enum import Enum


class FileTypeEnum(str, Enum):
    PROFILE = "Profile"
    CITIZENSHIP_FRONT = "CitizenshipFront"
    CITIZENSHIP_BACK = "CitizenshipBack"
    MISTRI_CERTIFICATE = "Certificate"
    OTHER = "Other"
