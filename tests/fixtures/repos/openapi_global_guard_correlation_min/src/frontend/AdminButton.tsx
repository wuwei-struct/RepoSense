export function AdminButton(props: { permissions: string[] }) {
  const canDelete = props.permissions.includes('users:delete');
  return <button disabled={!canDelete}>Delete user</button>;
}
