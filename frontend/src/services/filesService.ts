import api from './api';

export interface FileItem {
  name: string;
  path: string;
  is_dir: boolean;
  size: number;
  modified_time: string;
  created_time: string;
  extension: string;
  mime_type: string;
}

export interface UploadResponse {
  message: string;
  file: FileItem;
}

export interface CreateFolderResponse {
  message: string;
  folder: FileItem;
}

export interface RenameResponse {
  message: string;
  item: FileItem;
}

export interface CreateFileResponse {
  message: string;
  file: FileItem;
}

export interface FileContentResponse {
  content: string;
}

export const filesService = {
  // List files and folders in a directory
  async listFiles(path: string = ""): Promise<FileItem[]> {
    const response = await api.get('/files/', {
      params: { path }
    });
    return response.data;
  },

  // Upload a file
  async uploadFile(file: File, path: string = ""): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('path', path);

    const response = await api.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Create a new folder
  async createFolder(name: string, path: string = ""): Promise<CreateFolderResponse> {
    const params = new URLSearchParams();
    params.append('name', name);
    params.append('path', path);

    const response = await api.post('/files/create-folder', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    return response.data;
  },

  // Download a file
  async downloadFile(filePath: string): Promise<Blob> {
    const response = await api.get(`/files/download/${filePath}`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // Delete a file or folder
  async deleteItem(itemPath: string): Promise<{ message: string }> {
    const response = await api.delete(`/files/${itemPath}`);
    return response.data;
  },

  // Rename a file or folder
  async renameItem(oldPath: string, newName: string): Promise<RenameResponse> {
    const params = new URLSearchParams();
    params.append('old_path', oldPath);
    params.append('new_name', newName);

    const response = await api.put('/files/rename', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    return response.data;
  },

  // Search for files and folders
  async searchFiles(query: string, path: string = ""): Promise<FileItem[]> {
    const response = await api.get('/files/search', {
      params: { query, path }
    });
    return response.data;
  },

  // Create a new file
  async createFile(name: string, content: string, path: string = ""): Promise<CreateFileResponse> {
    const params = new URLSearchParams();
    params.append('name', name);
    params.append('content', content);
    params.append('path', path);

    const response = await api.post('/files/create-file', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    return response.data;
  },

  // Get file content
  async getFileContent(filePath: string): Promise<string> {
    const response = await api.get(`/files/content/${filePath}`);
    return response.data.content;
  },

  // Update file content
  async updateFileContent(filePath: string, content: string): Promise<{ message: string }> {
    const params = new URLSearchParams();
    params.append('content', content);

    const response = await api.put(`/files/content/${filePath}`, params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    return response.data;
  },

  // Helper function to format file size
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },

  // Helper function to get file icon based on type
  getFileIcon(file: FileItem): string {
    if (file.is_dir) return '📁';
    
    const extension = file.extension.toLowerCase();
    
    // Text files
    if (['.txt', '.md', '.log'].includes(extension)) return '📄';
    if (['.py', '.js', '.ts', '.sh', '.bash'].includes(extension)) return '📝';
    if (['.json', '.xml', '.yaml', '.yml'].includes(extension)) return '⚙️';
    if (['.sql'].includes(extension)) return '🗄️';
    
    // Documents
    if (['.pdf'].includes(extension)) return '📕';
    if (['.docx', '.doc'].includes(extension)) return '📘';
    if (['.xlsx', '.xls'].includes(extension)) return '📗';
    if (['.pptx', '.ppt'].includes(extension)) return '📙';
    
    // Images
    if (['.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico'].includes(extension)) return '🖼️';
    
    // Videos
    if (['.mp4', '.avi', '.mov'].includes(extension)) return '🎥';
    
    // Audio
    if (['.mp3', '.wav', '.flac'].includes(extension)) return '🎵';
    
    // Archives
    if (['.zip', '.tar', '.gz', '.tgz', '.rar'].includes(extension)) return '📦';
    
    // Web files
    if (['.html', '.css'].includes(extension)) return '🌐';
    
    // Configuration files
    if (['.conf', '.ini', '.cfg'].includes(extension)) return '⚙️';
    
    return '📄'; // Default file icon
  },

  // Helper function to check if file is previewable
  isPreviewable(file: FileItem): boolean {
    if (file.is_dir) return false;
    
    const previewableExtensions = [
      '.txt', '.md', '.log', '.py', '.js', '.ts', '.sh', '.bash',
      '.json', '.xml', '.yaml', '.yml', '.sql', '.html', '.css',
      '.conf', '.ini', '.cfg', '.csv'
    ];
    
    return previewableExtensions.includes(file.extension.toLowerCase());
  }
}; 