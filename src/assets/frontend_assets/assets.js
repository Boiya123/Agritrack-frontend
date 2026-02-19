import basket_icon from './basket_icon.png'
import logo from './logo.png'
import header_img from './header_farm.png'
import search_icon from './search_icon.png'
import menu_1 from './menu_1.png'
import menu_2 from './menu_2.png'
import menu_3 from './native_eggs.png'
import menu_4 from './seafood.png'
import menu_5 from './native_lamb.png'
import menu_6 from './white_pig.png'
import menu_7 from './native_turkey.png'
import menu_8 from './nattive_rabbits.png'

import food_1 from './Darag.png'
import food_2 from './Leg Horn Chicken.png'
import food_3 from './eggs.webp'
import food_4 from './DekalbWhite.png'
import food_5 from './ISABrown.jpg'
import food_6 from './native_black_pig.png'
import food_7 from './native_brown_chicken.png'
import food_8 from './native_cows.png'
import food_9 from './native_eggs.png'
import food_10 from './native_lamb.png'
import food_11 from './white_pig.png'
import food_12 from './nattive_rabbits.png'
import food_13 from './native_turkey.png'
import food_14 from './native_goat.png'
import food_15 from './bangus.png'
import food_16 from './tuna.png'
import food_17 from './salmon.png'
import food_18 from './shrimp.png'
import food_19 from './tilapia.png'
import food_20 from './crab.png'

import add_icon_white from './add_icon_white.png'
import add_icon_green from './add_icon_green.png'
import remove_icon_red from './remove_icon_red.png'
import app_store from './app_store.png'
import play_store from './play_store.png'
import linkedin_icon from './linkedin_icon.png'
import facebook_icon from './facebook_icon.png'
import twitter_icon from './twitter_icon.png'
import cross_icon from './cross_icon.png'
import selector_icon from './selector_icon.png'
import rating_starts from './rating_starts.png'
import profile_icon from './profile_icon.png'
import bag_icon from './bag_icon.png'
import logout_icon from './logout_icon.png'
import parcel_icon from './parcel_icon.png'

export const assets = {
    logo,
    basket_icon,
    header_img,
    search_icon,
    rating_starts,
    add_icon_green,
    add_icon_white,
    remove_icon_red,
    app_store,
    play_store,
    linkedin_icon,
    facebook_icon,
    twitter_icon,
    cross_icon,
    selector_icon,
    profile_icon,
    logout_icon,
    bag_icon,
    parcel_icon
}

export const menu_list = [
    { menu_name: "Chicken", menu_image: menu_1 },
    { menu_name: "Cattle", menu_image: menu_2 },
    { menu_name: "Eggs", menu_image: menu_3 },
    { menu_name: "Seafood", menu_image: menu_4 },
    { menu_name: "Lamb & Goat", menu_image: menu_5 },
    { menu_name: "Pork", menu_image: menu_6 },
    { menu_name: "Turkey", menu_image: menu_7 },
    { menu_name: "Rabbit", menu_image: menu_8 }
]

export const food_list = [
    {
        _id: "1",
        name: "Darag Chicken",
        image: food_1,
        price: 12,
        description: "Native Darag chicken known for its rich flavor, firm texture, and premium quality meat.",
        category: "Chicken"
    },
    {
        _id: "2",
        name: "Leghorn Chicken",
        image: food_2,
        price: 18,
        description: "Hardy chicken breed valued for its lean meat and high egg productivity.",
        category: "Chicken"
    },
    {
        _id: "3",
        name: "Fresh Farm Eggs",
        image: food_3,
        price: 16,
        description: "Nutritious farm-fresh eggs packed with protein and essential vitamins.",
        category: "Eggs"
    },
    {
        _id: "4",
        name: "Dekalb White",
        image: food_4,
        price: 24,
        description: "Hybrid layer breed known for consistent egg production and feed efficiency.",
        category: "Chicken"
    },
    {
        _id: "5",
        name: "ISA Brown",
        image: food_5,
        price: 14,
        description: "High-performing brown layer chicken adaptable to various climates.",
        category: "Chicken"
    },
    {
        _id: "6",
        name: "Native Black Pig",
        image: food_6,
        price: 22,
        description: "Premium native pork known for its rich taste and natural marbling.",
        category: "Pork"
    },
    {
        _id: "7",
        name: "Native Brown Chicken",
        image: food_7,
        price: 20,
        description: "Locally raised brown chicken with flavorful and tender meat.",
        category: "Chicken"
    },
    {
        _id: "8",
        name: "Native Cow",
        image: food_8,
        price: 30,
        description: "Grass-fed native cattle producing high-quality and lean beef.",
        category: "Cattle"
    },
    {
        _id: "9",
        name: "Native Eggs",
        image: food_9,
        price: 15,
        description: "Organic native eggs with richer yolk and enhanced flavor.",
        category: "Eggs"
    },
    {
        _id: "10",
        name: "Native Lamb",
        image: food_10,
        price: 28,
        description: "Tender and naturally raised lamb perfect for premium dishes.",
        category: "Lamb & Goat"
    },
    {
        _id: "11",
        name: "White Pig",
        image: food_11,
        price: 25,
        description: "High-quality pork from white pig breeds ideal for various recipes.",
        category: "Pork"
    },
    {
        _id: "12",
        name: "Native Rabbit",
        image: food_12,
        price: 19,
        description: "Lean and healthy rabbit meat known for its high protein content.",
        category: "Rabbit"
    },
    {
        _id: "13",
        name: "Native Turkey",
        image: food_13,
        price: 27,
        description: "Locally raised turkey with tender and flavorful meat.",
        category: "Turkey"
    },
    {
        _id: "14",
        name: "Native Goat",
        image: food_14,
        price: 26,
        description: "Fresh goat meat ideal for traditional and savory dishes.",
        category: "Lamb & Goat"
    },
    {
        _id: "15",
        name: "Bangus (Milkfish)",
        image: food_15,
        price: 12,
        description: "Fresh milkfish, a Filipino favorite known for its mild flavor.",
        category: "Seafood"
    },
    {
        _id: "16",
        name: "Tuna",
        image: food_16,
        price: 18,
        description: "Fresh tuna rich in omega-3 fatty acids and lean protein.",
        category: "Seafood"
    },
    {
        _id: "17",
        name: "Salmon",
        image: food_17,
        price: 24,
        description: "Premium salmon packed with healthy fats and nutrients.",
        category: "Seafood"
    },
    {
        _id: "18",
        name: "Shrimp",
        image: food_18,
        price: 20,
        description: "Fresh shrimp perfect for grilling, frying, or soups.",
        category: "Seafood"
    },
    {
        _id: "19",
        name: "Tilapia",
        image: food_19,
        price: 15,
        description: "Freshwater fish known for its mild taste and versatility.",
        category: "Seafood"
    },
    {
        _id: "20",
        name: "Crab",
        image: food_20,
        price: 22,
        description: "Fresh crab with sweet and succulent meat.",
        category: "Seafood"
    }
]
