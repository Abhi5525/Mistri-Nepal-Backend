from enum import Enum


class FileTypeEnum(str, Enum):
    PROFILE = "Profile"
    MISTRI_CERTIFICATE = "Certificate"
    OTHER = "Other"
