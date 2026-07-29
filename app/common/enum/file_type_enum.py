from enum import Enum


class FileTypeEnum(str, Enum):
    PROFILE = "Profile"
    CITIZENSHIP_FRONT = "Citizenship Front"
    CITIZENSHIP_BACK = "Citizenship Back"
    MISTRI_CERTIFICATE = "Certificate"
    OTHER = "Other"
