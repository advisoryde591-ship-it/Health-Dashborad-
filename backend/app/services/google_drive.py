"""Google Drive service for monitoring and downloading screenshots."""
import os
import io
from datetime import datetime, timedelta
from typing import Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from ..config import get_settings

settings = get_settings()

# Scopes required for Google Drive access
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


class GoogleDriveService:
    """Service for interacting with Google Drive."""

    def __init__(self):
        self.credentials = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Drive API."""
        creds = None

        # Load existing token if available
        if os.path.exists(settings.GOOGLE_TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(
                settings.GOOGLE_TOKEN_FILE, SCOPES
            )

        # If no valid credentials, initiate auth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(settings.GOOGLE_CREDENTIALS_FILE):
                    raise FileNotFoundError(
                        f"Google credentials file not found: {settings.GOOGLE_CREDENTIALS_FILE}"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    settings.GOOGLE_CREDENTIALS_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials for next run
            with open(settings.GOOGLE_TOKEN_FILE, "w") as token:
                token.write(creds.to_json())

        self.credentials = creds
        self.service = build("drive", "v3", credentials=creds)

    def list_files_in_folder(
        self,
        folder_id: Optional[str] = None,
        modified_after: Optional[datetime] = None,
        file_types: list = None,
    ) -> list:
        """List files in a Google Drive folder.

        Args:
            folder_id: Google Drive folder ID (uses config default if not provided)
            modified_after: Only return files modified after this datetime
            file_types: List of mime types to filter (e.g., ['image/png', 'image/jpeg'])

        Returns:
            List of file metadata dictionaries
        """
        folder_id = folder_id or settings.GOOGLE_DRIVE_FOLDER_ID

        if not folder_id:
            raise ValueError("No Google Drive folder ID configured")

        # Build query
        query_parts = [f"'{folder_id}' in parents", "trashed = false"]

        if modified_after:
            # Format datetime for Google Drive API
            modified_str = modified_after.strftime("%Y-%m-%dT%H:%M:%S")
            query_parts.append(f"modifiedTime > '{modified_str}'")

        if file_types:
            type_conditions = " or ".join(
                [f"mimeType = '{mt}'" for mt in file_types]
            )
            query_parts.append(f"({type_conditions})")
        else:
            # Default to images
            query_parts.append(
                "(mimeType = 'image/png' or mimeType = 'image/jpeg' or mimeType = 'image/jpg')"
            )

        query = " and ".join(query_parts)

        results = (
            self.service.files()
            .list(
                q=query,
                pageSize=100,
                fields="files(id, name, mimeType, modifiedTime, createdTime)",
                orderBy="modifiedTime desc",
            )
            .execute()
        )

        return results.get("files", [])

    def download_file(self, file_id: str) -> bytes:
        """Download a file from Google Drive.

        Args:
            file_id: Google Drive file ID

        Returns:
            File contents as bytes
        """
        request = self.service.files().get_media(fileId=file_id)
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        file_buffer.seek(0)
        return file_buffer.read()

    def get_new_screenshots(self, hours_back: int = 24) -> list:
        """Get screenshots uploaded in the last N hours.

        Args:
            hours_back: Number of hours to look back

        Returns:
            List of (file_metadata, file_bytes) tuples
        """
        modified_after = datetime.utcnow() - timedelta(hours=hours_back)

        files = self.list_files_in_folder(
            modified_after=modified_after,
            file_types=["image/png", "image/jpeg"],
        )

        results = []
        for file_info in files:
            file_bytes = self.download_file(file_info["id"])
            results.append((file_info, file_bytes))

        return results

    def check_folder_exists(self, folder_id: Optional[str] = None) -> bool:
        """Check if the configured folder exists and is accessible.

        Args:
            folder_id: Optional folder ID to check

        Returns:
            True if folder is accessible
        """
        folder_id = folder_id or settings.GOOGLE_DRIVE_FOLDER_ID

        if not folder_id:
            return False

        try:
            self.service.files().get(
                fileId=folder_id, fields="id, name"
            ).execute()
            return True
        except Exception:
            return False


def setup_google_drive_credentials():
    """Interactive setup for Google Drive credentials.

    Call this function once to authenticate with Google and save credentials.
    """
    print("Setting up Google Drive authentication...")

    if not os.path.exists(settings.GOOGLE_CREDENTIALS_FILE):
        print(
            f"\nPlease download your Google credentials file and save it as: {settings.GOOGLE_CREDENTIALS_FILE}"
        )
        print("\nTo get credentials:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable the Google Drive API")
        print("4. Create OAuth 2.0 credentials (Desktop app)")
        print("5. Download the JSON file")
        return False

    try:
        service = GoogleDriveService()
        print("\nAuthentication successful!")

        # Test access
        if settings.GOOGLE_DRIVE_FOLDER_ID:
            if service.check_folder_exists():
                print(f"Folder access confirmed: {settings.GOOGLE_DRIVE_FOLDER_ID}")
            else:
                print("Warning: Could not access the configured folder")

        return True
    except Exception as e:
        print(f"Authentication failed: {e}")
        return False
