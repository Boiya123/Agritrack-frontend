import React from 'react'
import './Home.css'
import Header from '../../components/NavBar/Header/Header'
import ExploreMenu from '../../components/ExploreMenu/ExploreMenu'
import PoultryDisplay from '../../components/PoultryDisplay/PoultryDisplay'
import AppDownload from '../../components/AppDownload/AppDownload'

const Home = () => {

    const[category, setCategory] = React.useState('All');
  return (
    <div>
        <div id='header'><Header/></div>   
        <ExploreMenu category={category} setCategory={setCategory} />
        <PoultryDisplay category={category}/>
        <div id='mobile-app'><AppDownload/></div>
    </div>
  )
}

export default Home