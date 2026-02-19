import React from 'react'
import './Footer.css'
import { assets } from '../../assets/frontend_assets/assets'

const Footer = () => {
  return (
    <div className='footer' id ='footer'>
        <div className="footer-content">

            <div className="footer-content-left">
                 <img src={assets.logo} alt="Logo" />
                 <p>lorem ipsum dolor sit amet.</p>
                 <div className="footer-social-icons">
                    <img src={assets.facebook_icon} alt="Facebook" />
                    <img src={assets.twitter_icon} alt="Twitter" />
                    <img src={assets.linkedin_icon} alt="LinkedIn" />
                 </div>
            </div>

                <div className="footer-content-center">
                   <h2>Alpha Kappa Code</h2>
                <ul>
                    <li>Home</li>
                    <li>About Us</li>
                    <li>Delivery</li>
                    <li>Privacy Policy</li>
                </ul>

            </div>

            <div className="footer-content-right">
                <h2>Contact Us</h2>
                <ul>
                    <li>+1 234 567 890</li>
                    <li>info@alphakappacode.com</li>
                </ul>
            </div>

        
        </div>
        <hr />
        <p className="footer-copyright">© 2024 Alpha Kappa Code. All rights reserved.</p>
    </div>
  )
}

export default Footer