export function formatDate(value?: string) {
  if (!value) {
    return 'Pending';
  }

  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}

export function shortId(value: string, length = 10) {
  return value.length > length ? `${value.slice(0, length)}...` : value;
}
