/**
 * Download a string as a file
 */
export const downloadStringAsFile = (
  content: string,
  filename: string,
  mimeType: string
) => {
  if (typeof window === 'undefined') {
    throw new Error('File download is only supported in the browser.');
  }

  const blob = new Blob([content], { type: mimeType });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();

  setTimeout(() => {
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }, 100);
};
