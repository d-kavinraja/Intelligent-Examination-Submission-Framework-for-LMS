export const FILENAME_PATTERN = /^(\d{12})_([A-Z0-9]{2,10})\.(pdf|jpg|jpeg|png)$/i

export const validateFilename = (filename) => {
  const match = filename.match(FILENAME_PATTERN)
  if (match) {
    return {
      valid: true,
      registerNumber: match[1],
      subjectCode: match[2].toUpperCase()
    }
  }
  return {
    valid: false,
    error: 'Invalid filename format. Expected: {12-digit RegNo}_{SubjectCode}.{pdf|jpg|jpeg|png}'
  }
}

export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
