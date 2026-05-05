import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from fastapi import HTTPException, UploadFile

from starlette.concurrency import run_in_threadpool

# Upload image
async def upload_file_cloudinary(file: UploadFile, folder: str):
    """Upload file to Cloudinary"""

    try:
    # Read file content
        result = await run_in_threadpool(
            cloudinary.uploader.upload,
            file.file,
            folder=folder,
            resource_type="auto"
        )

        return result.get("secure_url") or result.get("url"), result.get("public_id")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# Delete image using public_id
async def delete_file_cloudinary(public_id: str):
    """Delete file from Cloudinary using public_id"""
    try:
        await run_in_threadpool(cloudinary.uploader.destroy, public_id, resource_type="auto")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Generate transformed URL
async def generate_url_cloudinary(public_id, width=None, height=None, crop="fill"):
    url, _ = cloudinary_url(public_id, width=width, height=height, crop=crop)
    return url
