import React, { useContext, useCallback } from 'react'
import './PoultryItem.css'
import { assets } from '../../assets/frontend_assets/assets'
import { StoreContext } from '../../context/StoreContext'
const PoultryItem = ({id, name, price, description, image, onClick}) => {
  const handleClick = useCallback(() => {
    if (onClick) {
      onClick(id, name);
    }
  }, [id, name, onClick]);

  return (
    <div 
      className='food-item'
      onClick={handleClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
        <div className = 'food-item-img-container'>
            <img className="food-item-img" src={image || assets.header_img} alt={name} />
        </div>
        <div className="food-item-info">
            <div className="food-item name-rating">
                <p>{name}</p>
            </div>
            <p className='food-item-description'>{description}</p>
        </div>
    </div>
  )
}

export default PoultryItem