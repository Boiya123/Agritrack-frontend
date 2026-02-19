import React, { useContext} from 'react'
import './PoultryItem.css'
import { assets } from '../../assets/frontend_assets/assets'
import { StoreContext } from '../../context/StoreContext'
const PoultryItem = ({id, name, price, description, image}) => {
  return (
    <div className='food-item'>
        <div className = 'food-item-img-container'>
            <img className="food-item-img" src={image || assets.header_img} alt='' />
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