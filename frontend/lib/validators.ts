export function isAllowedStudyFile(file: File): boolean {
  const extension = file.name.split(".").pop()?.toLowerCase();
  return extension === "pdf" || extension === "txt";
}
