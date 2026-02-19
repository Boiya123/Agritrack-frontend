import React, { useContext } from 'react'
import './Cart.css'
import { StoreContext } from '../../context/StoreContext'

const Cart = () => {
    const{cartItems, removeFromCart, getTotalCartAmount, getAllProducts} = useContext(StoreContext);
    const allProducts = getAllProducts();

  return (
    <div className='cart'>
        <div className="cart-items">
            <div className="cart-items-title">
                <p>Items</p>
                <p>Title</p>
                <p>Price</p>
                <p>Quantity</p>
                <p>Total</p>
                <p>Remove</p>
            </div>
            <br />
            <hr />
            {allProducts.map((item, index) => {
                if(cartItems[item._id] > 0){
                    const priceValue = typeof item.price === 'number' ? item.price : 0;
                    return (
                        <div className="cart-items-title cart-items-item" key={item._id}>
                            <img src={item.image} alt={item.name} />
                            <p>{item.name}</p>
                            <p>{typeof item.price === 'number' ? `$${item.price}` : 'N/A'}</p>
                            <p>{cartItems[item._id]}</p>
                            <p>${(priceValue * cartItems[item._id])}</p>
                            <p onClick={() => removeFromCart(item._id)} className='cross'>x</p>
                        </div>
                    )
                }
                return null
            })}
        </div>
        <div className="cart-bottom">
            <div className="cart-total">
                <h2>Cart Total</h2>
                <div>
                    <div className="cart-total-details">
                        <p>Subtotal</p>
                        <p>{getTotalCartAmount()}</p>
                    </div>
                    <hr />
                    <div className="cart-total-details">
                        <p>Delivery Fee</p>     
                        <p>{2}</p>
                    </div>
                    <hr />
                    <div className="cart-total-details">
                        <b>Total</b>
                        <b>{getTotalCartAmount() + 2}</b>
                    </div>
                </div>
            </div>
        </div>
    </div>
  )
}

export default Cart