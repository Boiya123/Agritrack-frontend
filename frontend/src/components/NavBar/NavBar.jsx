import React, { useContext, useEffect } from 'react'
import './NavBar.css'
import { assets } from '../../assets/frontend_assets/assets'
import { Link, useLocation } from 'react-router-dom'
import { StoreContext } from '../../context/StoreContext'

const NavBar = ({ setShowLogin }) => {

    const [menu, setMenu] = React.useState("home");
    const {currentUser, logout} = useContext(StoreContext);
    const location = useLocation();

    // Update menu based on current route
    useEffect(() => {
        if (location.pathname === '/') {
            setMenu('home');
        } else if (location.pathname === '/ops') {
            setMenu('ops');
        } else if (location.pathname === '/dashboard') {
            setMenu('dashboard');
        }
    }, [location.pathname]);

    const handleSectionClick = (sectionId) => {
        // Scroll to section after a brief delay
        setTimeout(() => {
            const element = document.getElementById(sectionId);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth' });
            }
        }, 300);
    };

  return (
    <div className='navbar'>
        <Link to='/' onClick={() => setMenu("home")}><img className='logo' src={assets.logo} alt="logo" /></Link>

        <ul className='navbar-menu'>
            <Link to='/' style={{textDecoration: 'none'}}><li onClick={() => setMenu("home")} className={menu === "home" ? "active" : ""}>Home</li></Link>
            <Link to='/' style={{textDecoration: 'none'}}><li onClick={() => {setMenu("poultries"); handleSectionClick("poultry-display");}} className={menu === "poultries" ? "active" : ""}>Poultries</li></Link>
            <Link to='/' style={{textDecoration: 'none'}}><li onClick={() => {setMenu("mobile_app"); handleSectionClick("mobile-app");}} className={menu === "mobile_app" ? "active" : ""}>Mobile App</li></Link>
            <Link to='/' style={{textDecoration: 'none'}}><li onClick={() => {setMenu("contact_us"); handleSectionClick("footer");}} className={menu === "contact_us" ? "active" : ""}>Contact Us</li></Link>
            <Link to='/ops' style={{textDecoration: 'none'}}><li onClick={() => setMenu("ops")} className={menu === "ops" ? "active" : ""}>Operations</li></Link>
            <Link to='/dashboard' style={{textDecoration: 'none'}}><li onClick={() => setMenu("dashboard")} className={menu === "dashboard" ? "active" : ""}>Dashboard</li></Link>
        </ul>
        <div className='navbar-right'>
            <img src={assets.search_icon} alt="Search" />
            {currentUser ? (
                <div className='navbar-user'>
                    <span>{currentUser.email || 'Signed in'}</span>
                    <button onClick={logout}>Sign out</button>
                </div>
            ) : (
                <button onClick={() => setShowLogin(true)}>Sign In</button>
            )}
        </div>
    </div>
  )
}

export default NavBar