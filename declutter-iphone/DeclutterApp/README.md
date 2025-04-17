# Declutter App

A React Native mobile app for the Declutter platform. This app allows users to manage items they want to sell or give away, track claimed items, and complete transactions.

## Features

- User authentication (signup, login, logout)
- View available items
- Claim items
- Track claimed items
- Mark items as complete
- User profile management

## Prerequisites

- Node.js (v14 or newer)
- npm or Yarn
- Expo CLI
- iOS Simulator (for iOS) or Android Emulator (for Android)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd declutter-iphone/DeclutterApp
```

2. Install dependencies:
```bash
npm install
# or 
yarn install
```

3. Set up environment variables:
Create a `.env` file in the root directory with the following content:
```
EXPO_PUBLIC_SUPABASE_URL=your_supabase_url
EXPO_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

Note: This app uses react-native-dotenv to load environment variables. They are loaded from the `.env` file at the root of the DeclutterApp project. The variable names must start with EXPO_PUBLIC_ to be accessible in the app code.

## Running the App

1. Start the development server:
```bash
npm start
# or
yarn start
```

2. Follow the instructions in the terminal to open the app on your desired platform (iOS or Android).

3. If you make changes to environment variables, clear the cache:
```bash
expo start -c
# or
npm start -- --reset-cache
```

## Project Structure

- `src/components/` - UI components
- `src/screens/` - Screen components
- `src/lib/` - Utility functions and services
- `src/assets/` - Images and other static assets
- `src/types/` - TypeScript type definitions

## Database Schema

The app is designed to work with the following Supabase tables:

### profiles
- id (UUID, primary key)
- username (text)
- avatar_url (text)
- website (text)
- updated_at (timestamp)

### items
- id (int, primary key)
- name (text)
- description (text)
- price (numeric)
- status (text) - One of: 'available', 'claimed', 'complete'
- user_id (UUID, foreign key to profiles.id)
- created_at (timestamp)
- updated_at (timestamp)

## Connecting to Your Existing Supabase Backend

1. Obtain your Supabase URL and anon key from your Supabase project dashboard.
2. Add these values to the `.env` file as described in the Installation section.

## Future Improvements

- Add image upload support for items
- Implement push notifications
- Add search and filtering functionality
- Implement direct messaging between users

## License

[MIT License](LICENSE) 