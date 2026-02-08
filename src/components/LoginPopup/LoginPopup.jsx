import React, { useState } from 'react'
import './LoginPopup.css'
import { assets } from '../../assets/frontend_assets/assets'

const LoginPopup = ({ setShowLogin }) => {

  const [currState, setCurrState] = useState('Login');

  return (
    <div className='login-popup'>
        <form className='login-popup-container'>
          <div className='login-popup-title'>
            <h2>{currState}</h2>
            <img
              src={assets.cross_icon}
              alt='Close'
              onClick={() => setShowLogin(false)}
            />
          </div>
          <div className='login-popup-input'>
               {currState === "Sign Up" && (
                 <input type="text" placeholder='Your name' required/>
               )}
               <input type="email" placeholder='Your email' required/>
               <input type="password" placeholder='Your password' required/>
          </div>

          <button>{currState === "Sign Up" ? "Create Account" : "Log In"}</button>

          <div className="login-popup-condition">
            <input type="checkbox" required />
            <p>By continuing I agree to the Terms of Service and Privacy Policy.</p>
          </div>

          {currState === "Login"
          ?<p>Create Account? <span onClick={() => setCurrState("Sign Up")}>Click here</span></p>
          :<p>Already have an account? <span onClick={() => setCurrState("Login")}>Login Here</span></p>
          }



        </form>
    </div>
  )
}

export default LoginPopup