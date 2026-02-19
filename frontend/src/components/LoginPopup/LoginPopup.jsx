import React, { useContext, useState } from 'react'
import './LoginPopup.css'
import { assets } from '../../assets/frontend_assets/assets'
import { StoreContext } from '../../context/StoreContext'

const LoginPopup = ({ setShowLogin }) => {

  const [currState, setCurrState] = useState('Login');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    role: 'FARMER'
  });
  const [formError, setFormError] = useState('');
  const { login, register, authLoading, authError } = useContext(StoreContext);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setFormError('');
    try {
      if (currState === 'Sign Up') {
        if (!formData.name.trim()) {
          setFormError('Please enter your name.');
          return;
        }
        await register({
          name: formData.name.trim(),
          email: formData.email.trim(),
          password: formData.password,
          role: formData.role
        });
      } else {
        await login({
          email: formData.email.trim(),
          password: formData.password
        });
      }
      setShowLogin(false);
    } catch (error) {
      setFormError(error.message || 'Something went wrong.');
    }
  };

  return (
    <div className='login-popup'>
        <form className='login-popup-container' onSubmit={handleSubmit}>
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
                 <input
                  type="text"
                  name="name"
                  placeholder='Your name'
                  value={formData.name}
                  onChange={handleChange}
                  required
                />
               )}
               <input
                type="email"
                name="email"
                placeholder='Your email'
                value={formData.email}
                onChange={handleChange}
                required
              />
               <input
                type="password"
                name="password"
                placeholder='Your password'
                value={formData.password}
                onChange={handleChange}
                required
              />
               {currState === "Sign Up" && (
                 <select name="role" value={formData.role} onChange={handleChange} required>
                   <option value="FARMER">Farmer</option>
                   <option value="SUPPLIER">Supplier</option>
                   <option value="REGULATOR">Regulator</option>
                   <option value="ADMIN">Admin</option>
                 </select>
               )}
          </div>
          {(formError || authError) && (
            <div className='login-popup-error'>{formError || authError}</div>
          )}

          <button disabled={authLoading}>
            {authLoading ? 'Please wait...' : currState === "Sign Up" ? "Create Account" : "Log In"}
          </button>

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