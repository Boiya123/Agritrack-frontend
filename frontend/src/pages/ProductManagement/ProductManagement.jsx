import React, { useState, useContext, useEffect } from 'react'
import './ProductManagement.css'
import { StoreContext } from '../../context/StoreContext'
import { productsApi } from '../../api'
import RoleGate from '../../components/RoleGate/RoleGate'

/**
 * Product Management Page (Admin Only)
 * 
 * This page lets admins:
 * - View all products
 * - Edit product descriptions
 * - Enable/disable products
 * - Create new products
 * 
 * Only admins can access this. We use RoleGate to enforce it.
 */
const ProductManagement = () => {
  const { authToken, currentUser, products, loadProducts } = useContext(StoreContext)

  const [editingProductId, setEditingProductId] = useState(null)
  const [editForm, setEditForm] = useState({ description: '' })
  const [message, setMessage] = useState({ type: '', text: '' })
  const [loading, setLoading] = useState(false)

  // Load products on mount
  useEffect(() => {
    loadProducts()
  }, [])

  // Show message for 3 seconds
  const showMessage = (type, text) => {
    setMessage({ type, text })
    setTimeout(() => setMessage({ type: '', text: '' }), 3000)
  }

  // Start editing a product
  const startEdit = (product) => {
    setEditingProductId(product.id)
    setEditForm({ description: product.description })
  }

  // Cancel editing
  const cancelEdit = () => {
    setEditingProductId(null)
    setEditForm({ description: '' })
  }

  // Save product changes
  const handleSaveEdit = async (productId) => {
    setLoading(true)
    try {
      await productsApi.update(authToken, productId, {
        description: editForm.description
      })
      showMessage('success', 'Product updated successfully!')
      setEditingProductId(null)
      await loadProducts()
    } catch (error) {
      showMessage('error', error.message || 'Failed to update product.')
    } finally {
      setLoading(false)
    }
  }

  // Enable a product
  const handleEnable = async (productId) => {
    setLoading(true)
    try {
      await productsApi.enable(authToken, productId)
      showMessage('success', 'Product enabled!')
      await loadProducts()
    } catch (error) {
      showMessage('error', error.message || 'Failed to enable product.')
    } finally {
      setLoading(false)
    }
  }

  // Disable a product
  const handleDisable = async (productId) => {
    setLoading(true)
    try {
      await productsApi.disable(authToken, productId)
      showMessage('success', 'Product disabled!')
      await loadProducts()
    } catch (error) {
      showMessage('error', error.message || 'Failed to disable product.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <RoleGate currentUser={currentUser} allowedRoles={['ADMIN']}>
      <div className='product-management'>
        <header className='pm-header'>
          <div>
            <h1>Product Management</h1>
            <p>Manage all product types in the system.</p>
          </div>
        </header>

        {message.text && (
          <div className={`message ${message.type}`}>
            {message.text}
          </div>
        )}

        {products.length === 0 ? (
          <div className='empty-state'>
            <p>No products yet. Create one in the " Add Product" page.</p>
          </div>
        ) : (
          <div className='products-table'>
            <table>
              <thead>
                <tr>
                  <th>Product Name</th>
                  <th>Description</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {products.map((product) => (
                  <tr key={product.id} className={!product.is_active ? 'disabled' : ''}>
                    <td className='product-name'>
                      <strong>{product.name}</strong>
                    </td>
                    <td className='product-description'>
                      {editingProductId === product.id ? (
                        <textarea
                          value={editForm.description}
                          onChange={(e) =>
                            setEditForm({ ...editForm, description: e.target.value })
                          }
                          placeholder='Enter product description'
                        />
                      ) : (
                        <span>{product.description || 'No description'}</span>
                      )}
                    </td>
                    <td className='status'>
                      <span className={`badge ${product.is_active ? 'active' : 'inactive'}`}>
                        {product.is_active ? '✅ Active' : '❌ Inactive'}
                      </span>
                    </td>
                    <td className='actions'>
                      {editingProductId === product.id ? (
                        <>
                          <button
                            className='btn-save'
                            onClick={() => handleSaveEdit(product.id)}
                            disabled={loading}
                          >
                            Save
                          </button>
                          <button
                            className='btn-cancel'
                            onClick={cancelEdit}
                            disabled={loading}
                          >
                            Cancel
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            className='btn-edit'
                            onClick={() => startEdit(product)}
                            disabled={loading}
                          >
                            Edit
                          </button>
                          {product.is_active ? (
                            <button
                              className='btn-disable'
                              onClick={() => handleDisable(product.id)}
                              disabled={loading}
                            >
                              Disable
                            </button>
                          ) : (
                            <button
                              className='btn-enable'
                              onClick={() => handleEnable(product.id)}
                              disabled={loading}
                            >
                              Enable
                            </button>
                          )}
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </RoleGate>
  )
}

export default ProductManagement
