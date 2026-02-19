import React, { useState, useContext } from 'react'
import './AddProduct.css'
import { StoreContext } from '../../context/StoreContext'
import RoleGate from '../../components/RoleGate/RoleGate'

// This page is ADMIN ONLY. We use RoleGate to protect it.
// If a non-admin tries to access it, they'll see an access denied message.
const AddProduct = () => {
  const { createProduct, currentUser } = useContext(StoreContext)
  
  const [formData, setFormData] = useState({
    name: '',
    description: ''
  })

  const [successMessage, setSuccessMessage] = useState('')
  const [errorMessage, setErrorMessage] = useState('')

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData({
      ...formData,
      [name]: value
    })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    setSuccessMessage('')
    setErrorMessage('')

    if (!formData.name || !formData.description) {
      setErrorMessage('Please fill all fields.')
      return
    }

    createProduct({
      name: formData.name.trim(),
      description: formData.description.trim()
    })
      .then(() => {
        setSuccessMessage('Product type created successfully!')
        setFormData({
          name: '',
          description: ''
        })
        setTimeout(() => {
          setSuccessMessage('')
        }, 3000)
      })
      .catch((error) => {
        setErrorMessage(error.message || 'Unable to create product type.')
      })
  }

  return (
    <RoleGate currentUser={currentUser} allowedRoles={['ADMIN']}>
      <div className='add-product'>
        <div className='add-product-container'>
          <h1>Create Product Type</h1>
          <p>Define a product type for traceability (poultry, fish, rice, etc.).</p>

          {successMessage && <div className='success-message'>{successMessage}</div>}
          {errorMessage && <div className='error-message'>{errorMessage}</div>}

          <form onSubmit={handleSubmit} className='product-form'>
            <div className='form-group'>
              <label htmlFor='name'>Product Type Name *</label>
              <input
                type='text'
                id='name'
                name='name'
                value={formData.name}
                onChange={handleInputChange}
                placeholder='Example: Poultry - Broiler'
                required
              />
            </div>

            <div className='form-group'>
              <label htmlFor='description'>Description *</label>
              <textarea
                id='description'
                name='description'
                value={formData.description}
                onChange={handleInputChange}
                placeholder='Describe how this product type is produced and tracked.'
                rows='5'
                required
              ></textarea>
            </div>
            <button type='submit' className='submit-btn'>Create Product Type</button>
          </form>
        </div>
      </div>
    </RoleGate>
  )
}

export default AddProduct
