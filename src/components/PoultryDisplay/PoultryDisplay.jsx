import React, { useContext } from 'react'
import './PoultryDisplay.css'
import PoultryItem from '../PoultryItem/PoultryItem';
import { StoreContext } from '../../context/StoreContext';

const PoultryDisplay = ({ category }) => {

    const {food_list, getAllProducts} = useContext(StoreContext);
    const allProducts = getAllProducts();

  return (
    <div className='poultry-display' id ='poultry-display'>
        <h2>Our Poultry Products</h2>
        <div className="food-display-list">
            {allProducts.map ((item, index) =>{
                if(category === 'All' || item.category === category){
                    return <PoultryItem key={item._id ?? index} id={item._id} name={item.name} price={item.price} description={item.description} image={item.image} />
                }
            })}
        </div>

    </div>
  )
}

export default PoultryDisplay