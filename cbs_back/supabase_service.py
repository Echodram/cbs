from supabase import create_client
from django.conf import settings

class SupabaseStorageService:
    def __init__(self):
        self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        self.bucket_name = 'your-bucket-name'

    def upload_file(self, file_obj):
        file_path = f"uploads/{file_obj.name}"
        content = file_obj.read()
        response = self.supabase.storage.from_(self.bucket_name).upload(file_path, content)
        if response.get('error'):
            raise Exception(response['error']['message'])
        # Construct a public URL (assuming bucket is public or signed URL)
        public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{self.bucket_name}/{file_path}"
        return public_url
    
    def download_file(self, file_path):
        pass
    
    def delete_file(self, file_path):
        pass