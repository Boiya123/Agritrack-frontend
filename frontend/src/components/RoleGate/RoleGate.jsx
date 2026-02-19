import React from 'react'
import './RoleGate.css'

/**
 * RoleGate Component
 * 
 * This is a simple permission checker. It hides content if the user doesn't have the right role.
 * Saves us from having to check roles in every single page.
 * 
 * Usage:
 * <RoleGate allowedRoles={['ADMIN', 'REGULATOR']}>
 *   <AdminOnlyComponent />
 * </RoleGate>
 */
const RoleGate = ({ currentUser, allowedRoles, children, fallback }) => {
  // Check if user has permission
  if (!currentUser) {
    return fallback || (
      <div className='role-gate-error'>
        <h2>Access Denied</h2>
        <p>Please sign in first.</p>
      </div>
    )
  }

  // Check if user's role is in the allowed list
  const userRole = String(currentUser.role).toUpperCase()
  const hasPermission = allowedRoles.some(role => role.toUpperCase() === userRole)

  if (!hasPermission) {
    return fallback || (
      <div className='role-gate-error'>
        <h2>Access Denied</h2>
        <p>This area is only for: <strong>{allowedRoles.join(', ')}</strong></p>
        <p>Your role: <strong>{currentUser.role}</strong></p>
      </div>
    )
  }

  // User is authorized, show content
  return <>{children}</>
}

export default RoleGate
