import { createContext, useEffect, useState, useCallback, useMemo } from 'react';
import { food_list, assets } from '../assets/frontend_assets/assets';
import { authApi, productsApi } from '../api';

export const StoreContext = createContext(null);

const StoreContextProvider = (props) => {
    const [cartItems, setCartItems] = useState({});
    const [authToken, setAuthToken] = useState(() => localStorage.getItem('agritrack_token') || '');
    const [currentUser, setCurrentUser] = useState(() => {
        const saved = localStorage.getItem('agritrack_user');
        return saved ? JSON.parse(saved) : null;
    });
    const [authLoading, setAuthLoading] = useState(false);
    const [authError, setAuthError] = useState('');

    const [products, setProducts] = useState([]);
    const [productsLoading, setProductsLoading] = useState(false);
    const [productsError, setProductsError] = useState('');

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

    const saveAuth = (token, user) => {
        setAuthToken(token || '');
        setCurrentUser(user || null);
        if (token) {
            localStorage.setItem('agritrack_token', token);
        } else {
            localStorage.removeItem('agritrack_token');
        }
        if (user) {
            localStorage.setItem('agritrack_user', JSON.stringify(user));
        } else {
            localStorage.removeItem('agritrack_user');
        }
    };

    const login = async (payload) => {
        setAuthLoading(true);
        setAuthError('');
        try {
            const data = await authApi.login(payload);
            let profile = null;
            try {
                profile = await authApi.me(data.access_token);
            } catch (profileError) {
                profile = {
                    id: data.user_id,
                    role: data.role,
                    email: payload.email
                };
            }
            saveAuth(data.access_token, profile);
            return data;
        } catch (error) {
            setAuthError(error.message || 'Login failed');
            throw error;
        } finally {
            setAuthLoading(false);
        }
    };

    const register = async (payload) => {
        setAuthLoading(true);
        setAuthError('');
        try {
            await authApi.register(payload);
            const data = await login({ email: payload.email, password: payload.password });
            return data;
        } catch (error) {
            setAuthError(error.message || 'Registration failed');
            throw error;
        } finally {
            setAuthLoading(false);
        }
    };

    const logout = async () => {
        if (authToken) {
            try {
                await authApi.logout(authToken);
            } catch (error) {
                // Ignore logout failures so local sign-out still works.
            }
        }
        saveAuth('', null);
    };

    const loadProducts = useCallback(async () => {
        if (!authToken) {
            setProducts([]);
            return;
        }
        setProductsLoading(true);
        setProductsError('');
        try {
            const data = await productsApi.list(authToken, { active_only: true });
            setProducts(data || []);
        } catch (error) {
            setProductsError(error.message || 'Failed to load products');
        } finally {
            setProductsLoading(false);
        }
    }, [authToken]);

    const createProduct = async (payload) => {
        if (!authToken) {
            throw new Error('Please sign in to create products.');
        }
        const data = await productsApi.create(authToken, payload);
        await loadProducts();
        return data;
    };

    useEffect(() => {
        loadProducts();
    }, [loadProducts]);

    const mappedApiProducts = useMemo(() => {
        return products.map((product) => ({
            _id: product.id,
            name: product.name,
            price: null,
            description: product.description || 'No description provided yet.',
            category: 'All',
            image: assets.header_img,
            source: 'api'
        }));
    }, [products]);

    const getAllProducts = () => {
        return [...food_list, ...mappedApiProducts];
    }

    const getTotalCartAmount = () => {
        let totalAmount = 0;
        const allProducts = getAllProducts();
        for (const item in cartItems) {
            if (cartItems[item] > 0) {
                const itemInfo = allProducts.find((product) => product._id === item);
                if (itemInfo && typeof itemInfo.price === 'number') {
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
        authToken,
        currentUser,
        authLoading,
        authError,
        login,
        register,
        logout,
        products,
        productsLoading,
        productsError,
        loadProducts,
        createProduct,
        getAllProducts
    }
    return (
        <StoreContext.Provider value={contextValue}>
            {props.children}
        </StoreContext.Provider>
    )
}

export default StoreContextProvider;