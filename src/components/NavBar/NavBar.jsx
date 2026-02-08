import React, { useContext } from 'react'
import './NavBar.css'
import { assets } from '../../assets/frontend_assets/assets'
import { Link, useLocation } from 'react-router-dom'
import { StoreContext } from '../../context/StoreContext'

const NavBar = ({ setShowLogin }) => {

    const [menu, setMenu] = React.useState("home");
    const location = useLocation();

    const {getTotalCartAmount} = useContext(StoreContext);
    
    const handleMenuClick = (menuName, sectionId) => {
        setMenu(menuName);
        const element = document.getElementById(sectionId);
        if(element){
            element.scrollIntoView({behavior: 'smooth'});
        }
    };

    const handleSellClick = () => {
        setMenu("sell");
    };


  return (
    <div className='navbar'>
        <Link to='/' onClick={() => setMenu("home")}><img className='logo' src={assets.logo} alt="logo" /></Link>

        <ul className='navbar-menu'>
            <Link to='/' style={{textDecoration: 'none'}}><li onClick={() => setMenu("home")} className={menu === "home" ? "active" : ""}>Home</li></Link>
            <li onClick={() => handleMenuClick("poultries", "poultry-display")} className={menu === "poultries" ? "active" : ""}>Poultries</li>
            <li onClick={() => handleMenuClick("mobile_app", "mobile-app")} className={menu === "mobile_app" ? "active" : ""}>Mobile App</li>
            <li onClick={() => handleMenuClick("contact_us", "footer")} className={menu === "contact_us" ? "active" : ""}>Contact Us</li>
            <Link to='/add-product' style={{textDecoration: 'none'}}><li onClick={handleSellClick} className={menu === "sell" ? "active" : ""}>Sell</li></Link>
        </ul>
        <div className='navbar-right'>
            <img src={assets.search_icon} alt="Search" />
            <div className='navbar-search icon'>
                <Link to='/cart'> <img src={assets.basket_icon} alt="Search" /></Link>
                <div className={getTotalCartAmount() === 0 ? "" : "dot"}></div>
            </div>
            <button onClick={() => setShowLogin(true)}>sign In</button>
        </div>
    </div>
  )
}

export default NavBar