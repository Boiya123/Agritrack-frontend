import React, { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import NavBar from './components/NavBar/NavBar'
import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home/Home'
import AddProduct from './pages/AddProduct/AddProduct'
import Operations from './pages/Operations/Operations'
import Dashboard from './pages/Dashboard/Dashboard'
import RegulatoryDashboard from './pages/Dashboard/RegulatoryDashboard'
import AccountSettings from './pages/AccountSettings/AccountSettings'
import ProductManagement from './pages/ProductManagement/ProductManagement'
import BatchDetail from './pages/BatchDetail/BatchDetail'
import StoreContextProvider from './context/StoreContext'
import Footer from './components/Footer/Footer'
import LoginPopup from './components/LoginPopup/LoginPopup'

// This is the main app component. We added three new routes here:
// - /account: for users to manage their password and profile
// - /products: for admins to manage all product types
// - /batch/:batchId: for viewing detailed batch history and audit trail
const App = () => {

  const [showLogin, setShowLogin] = useState(false);
  const location = useLocation();

  // Scroll to top on route change
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [location.pathname]);

  return (
    <StoreContextProvider>
      {showLogin ? <LoginPopup setShowLogin={setShowLogin} /> : <></>}

      <div className='app'>
        <NavBar setShowLogin={setShowLogin} />
        <Routes>
          <Route path='/' element={<Home />} />
          <Route path='/add-product' element={<AddProduct />} />
          <Route path='/ops' element={<Operations />} />
          <Route path='/dashboard' element={<Dashboard />} />
          <Route path='/regulatory' element={<RegulatoryDashboard />} />
          <Route path='/account' element={<AccountSettings />} />
          <Route path='/products' element={<ProductManagement />} />
          <Route path='/batch/:batchId' element={<BatchDetail />} />
        </Routes>
      </div>
      <Footer />
    </StoreContextProvider>
  )
}

export default App