import React, { useState, useContext } from 'react'
import './AccountSettings.css'
import { StoreContext } from '../../context/StoreContext'
import { authApi } from '../../api'

/**
 * Account Settings Page
 * 
 * This page lets users:
 * - See their profile info
 * - Change their password
 * - Request a password reset (if they forgot it)
 * 
 * The backend already has these endpoints, we just needed to build the UI.
 */
const AccountSettings = () => {
  const { authToken, currentUser, logout } = useContext(StoreContext)

  // Form states
  const [changePasswordForm, setChangePasswordForm] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  })

  const [passwordResetEmail, setPasswordResetEmail] = useState('')

  // Feedback messages
  const [successMessage, setSuccessMessage] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [loading, setLoading] = useState(false)

  // Clear messages after 3 seconds
  const showMessage = (type, message) => {
    if (type === 'success') {
      setSuccessMessage(message)
      setTimeout(() => setSuccessMessage(''), 3000)
    } else {
      setErrorMessage(message)
      setTimeout(() => setErrorMessage(''), 3000)
    }
  }

  // Handle password change
  const handlePasswordChange = async (e) => {
    e.preventDefault()
    setLoading(true)

    // Quick validation
    if (!changePasswordForm.oldPassword || !changePasswordForm.newPassword) {
      showMessage('error', 'Please fill in all fields.')
      setLoading(false)
      return
    }

    if (changePasswordForm.newPassword !== changePasswordForm.confirmPassword) {
      showMessage('error', 'New passwords do not match.')
      setLoading(false)
      return
    }

    if (changePasswordForm.newPassword.length < 6) {
      showMessage('error', 'New password must be at least 6 characters.')
      setLoading(false)
      return
    }

    try {
      await authApi.passwordChange(
        authToken,
        changePasswordForm.oldPassword,
        changePasswordForm.newPassword
      )
      showMessage('success', 'Password changed successfully!')
      setChangePasswordForm({ oldPassword: '', newPassword: '', confirmPassword: '' })
    } catch (error) {
      showMessage('error', error.message || 'Failed to change password.')
    } finally {
      setLoading(false)
    }
  }

  // Handle password reset request
  const handlePasswordReset = async (e) => {
    e.preventDefault()
    setLoading(true)

    if (!passwordResetEmail) {
      showMessage('error', 'Please enter your email.')
      setLoading(false)
      return
    }

    try {
      await authApi.passwordReset(passwordResetEmail)
      showMessage('success', 'If an account exists with that email, you will receive a reset link.')
      setPasswordResetEmail('')
    } catch (error) {
      showMessage('error', error.message || 'Failed to request password reset.')
    } finally {
      setLoading(false)
    }
  }

  // Not signed in
  if (!authToken || !currentUser) {
    return (
      <div className='account-settings'>
        <div className='settings-card'>
          <h2>Sign In Required</h2>
          <p>Please sign in to access account settings.</p>
        </div>
      </div>
    )
  }

  return (
    <div className='account-settings'>
      <header className='settings-header'>
        <h1>Account Settings</h1>
        <p>Manage your profile and security.</p>
      </header>

      {successMessage && <div className='message success'>{successMessage}</div>}
      {errorMessage && <div className='message error'>{errorMessage}</div>}

      {/* Profile Section */}
      <section className='settings-card'>
        <h2>Your Profile</h2>
        <div className='profile-info'>
          <div className='info-row'>
            <span className='label'>Name:</span>
            <span className='value'>{currentUser.name || 'N/A'}</span>
          </div>
          <div className='info-row'>
            <span className='label'>Email:</span>
            <span className='value'>{currentUser.email}</span>
          </div>
          <div className='info-row'>
            <span className='label'>Role:</span>
            <span className='value'><strong>{currentUser.role}</strong></span>
          </div>
          <div className='info-row'>
            <span className='label'>Status:</span>
            <span className='value'>✅ Active</span>
          </div>
        </div>
      </section>

      {/* Change Password Section */}
      <section className='settings-card'>
        <h2>Change Password</h2>
        <form onSubmit={handlePasswordChange}>
          <div className='form-group'>
            <label htmlFor='oldPassword'>Current Password *</label>
            <input
              type='password'
              id='oldPassword'
              value={changePasswordForm.oldPassword}
              onChange={(e) =>
                setChangePasswordForm({ ...changePasswordForm, oldPassword: e.target.value })
              }
              placeholder='Enter your current password'
              required
            />
          </div>

          <div className='form-group'>
            <label htmlFor='newPassword'>New Password *</label>
            <input
              type='password'
              id='newPassword'
              value={changePasswordForm.newPassword}
              onChange={(e) =>
                setChangePasswordForm({ ...changePasswordForm, newPassword: e.target.value })
              }
              placeholder='Enter a new password (min 6 characters)'
              required
            />
          </div>

          <div className='form-group'>
            <label htmlFor='confirmPassword'>Confirm New Password *</label>
            <input
              type='password'
              id='confirmPassword'
              value={changePasswordForm.confirmPassword}
              onChange={(e) =>
                setChangePasswordForm({ ...changePasswordForm, confirmPassword: e.target.value })
              }
              placeholder='Re-enter your new password'
              required
            />
          </div>

          <button type='submit' disabled={loading}>
            {loading ? 'Updating...' : 'Update Password'}
          </button>
        </form>
      </section>

      {/* Password Reset Section */}
      <section className='settings-card'>
        <h2>Forgot Your Password?</h2>
        <p className='help-text'>
          Request a password reset link to be sent to your email. Only use this if you've forgotten your password.
        </p>
        <form onSubmit={handlePasswordReset}>
          <div className='form-group'>
            <label htmlFor='resetEmail'>Email Address *</label>
            <input
              type='email'
              id='resetEmail'
              value={passwordResetEmail}
              onChange={(e) => setPasswordResetEmail(e.target.value)}
              placeholder='Enter your email'
              required
            />
          </div>
          <button type='submit' disabled={loading}>
            {loading ? 'Sending...' : 'Send Reset Link'}
          </button>
        </form>
      </section>

      {/* Logout Section */}
      <section className='settings-card danger'>
        <h2>Logout</h2>
        <p className='help-text'>End your current session.</p>
        <button
          onClick={() => {
            logout()
            window.location.href = '/'
          }}
          className='logout-btn'
        >
          Logout
        </button>
      </section>
    </div>
  )
}

export default AccountSettings
