export function AdminButton({ user, onDelete }: any) {
  const allowed = user.isAdmin || user.permissions.includes("user:delete");
  return <button disabled={!allowed} onClick={onDelete}>Delete user</button>;
}

