import React, { useContext } from 'react'
import './PoultryDisplay.css'
import PoultryItem from '../PoultryItem/PoultryItem';
import { StoreContext } from '../../context/StoreContext';
const PoultryDisplay = ({ category }) => {
    const { getAllProducts } = useContext(StoreContext);
    const allProducts = getAllProducts().slice(0, 20); // Only show first 20 products
  return (
    <div className='poultry-display' id ='poultry-display'>
        <h2>Our Poultry Products</h2>
        <div className="food-display-list">
            {allProducts.map ((item, index) =>{
                const itemCategory = item.category || 'All';
                if(category === 'All' || itemCategory === category){
                    return <PoultryItem key={item._id ?? index} id={item._id} name={item.name} price={item.price} description={item.description} image={item.image} />
                }
            })}
        </div>

    </div>
  )
}
export default PoultryDisplay