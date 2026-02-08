import React, { useState, useContext } from 'react'
import './AddProduct.css'
import { StoreContext } from '../../context/StoreContext'

const AddProduct = () => {
  const { addUserProduct } = useContext(StoreContext)
  
  const [formData, setFormData] = useState({
    name: '',
    price: '',
    description: '',
    category: 'Chicken',
    imageBase64: ''
  })

  const [successMessage, setSuccessMessage] = useState('')

  const categories = ['Chicken', 'Cow', 'Deserts', 'Sandwich', 'Cake', 'Pure Veg', 'Pasta', 'Noodles']

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData({
      ...formData,
      [name]: value
    })
  }

  const handleImageChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      const reader = new FileReader()
      reader.onloadend = () => {
        setFormData({
          ...formData,
          imageBase64: reader.result
        })
      }
      reader.readAsDataURL(file)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()

    if (!formData.name || !formData.price || !formData.description || !formData.imageBase64) {
      alert('Please fill all fields and select an image')
      return
    }

    const newProduct = {
      _id: Date.now().toString(),
      name: formData.name,
      price: parseFloat(formData.price),
      description: formData.description,
      category: formData.category,
      image: formData.imageBase64
    }

    addUserProduct(newProduct)
    
    setSuccessMessage('Product added successfully!')
    setFormData({
      name: '',
      price: '',
      description: '',
      category: 'Chicken',
      imageBase64: ''
    })

    setTimeout(() => {
      setSuccessMessage('')
    }, 3000)
  }

  return (
    <div className='add-product'>
      <div className='add-product-container'>
        <h1>Add Your Product</h1>
        <p>Join our marketplace and start selling your poultry products today!</p>

        {successMessage && <div className='success-message'>{successMessage}</div>}

        <form onSubmit={handleSubmit} className='product-form'>
          <div className='form-group'>
            <label htmlFor='name'>Product Name *</label>
            <input
              type='text'
              id='name'
              name='name'
              value={formData.name}
              onChange={handleInputChange}
              placeholder='Enter product name'
              required
            />
          </div>

          <div className='form-group'>
            <label htmlFor='price'>Price ($) *</label>
            <input
              type='number'
              id='price'
              name='price'
              value={formData.price}
              onChange={handleInputChange}
              placeholder='0.00'
              step='0.01'
              min='0'
              required
            />
          </div>

          <div className='form-group'>
            <label htmlFor='category'>Category *</label>
            <select
              id='category'
              name='category'
              value={formData.category}
              onChange={handleInputChange}
              required
            >
              {categories.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          <div className='form-group'>
            <label htmlFor='description'>Description *</label>
            <textarea
              id='description'
              name='description'
              value={formData.description}
              onChange={handleInputChange}
              placeholder='Describe your product in detail'
              rows='5'
              required
            ></textarea>
          </div>

          <div className='form-group'>
            <label htmlFor='image'>Product Image *</label>
            <input
              type='file'
              id='image'
              name='image'
              onChange={handleImageChange}
              accept='image/*'
              required
            />
            {formData.imageBase64 && (
              <div className='image-preview'>
                <img src={formData.imageBase64} alt='Preview' />
              </div>
            )}
          </div>

          <button type='submit' className='submit-btn'>Add Product to Marketplace</button>
        </form>
      </div>
    </div>
  )
}

export default AddProduct
