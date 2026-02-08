import { createContext, useEffect, useState } from 'react';
import { food_list } from '../assets/frontend_assets/assets';

export const StoreContext = createContext(null);

const StoreContextProvider = (props) => {

    const [cartItems, setCartItems] = useState({});
    const [userProducts, setUserProducts] = useState(() => {
        const saved = localStorage.getItem('userProducts');
        return saved ? JSON.parse(saved) : [];
    });

    // Save user products to localStorage whenever they change
    useEffect(() => {
        localStorage.setItem('userProducts', JSON.stringify(userProducts));
    }, [userProducts]);

    const addToCart = (itemId) => {
        if (!cartItems[itemId]) {
            setCartItems((prev) => ({ ...prev, [itemId]: 1 }))
        }
        else {
            setCartItems((prev) => ({ ...prev, [itemId]: prev[itemId] + 1 }))
        }
    }

    const removeFromCart = (itemId) => {
        setCartItems((prev) => ({ ...prev, [itemId]: Math.max(prev[itemId] - 1, 0) }))
    }

    const addUserProduct = (product) => {
        setUserProducts((prev) => [...prev, product]);
    }

    const getAllProducts = () => {
        return [...food_list, ...userProducts];
    }

    const getTotalCartAmount = () => {
        let totalAmount = 0;
        const allProducts = getAllProducts();
        for (const item in cartItems) {
            if (cartItems[item] > 0) {
                let itemInfo = allProducts.find((product) => product._id === item);
                if (itemInfo) {
                    totalAmount += cartItems[item] * itemInfo.price;
                }
            }
        }
        return totalAmount;
    }

    const contextValue = {
        food_list,
        cartItems,
        setCartItems,
        addToCart,
        removeFromCart,
        getTotalCartAmount,
        userProducts,
        addUserProduct,
        getAllProducts
    }
    return (
        <StoreContext.Provider value={contextValue}>
            {props.children}
        </StoreContext.Provider>
    )
}

    export default StoreContextProvider;