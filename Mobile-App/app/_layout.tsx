import { Stack } from 'expo-router';
import { LinkingOptions } from '@react-navigation/native';

const linking: LinkingOptions = {
  prefixes: ['functiongrapher://', 'https://function-grapher.vercel.app'],
  config: {
    screens: {
      index: '',
      // Add other screens if you have them, e.g.:
      // about: 'about',
      // settings: 'settings',
    },
  },
};

export default function RootLayout() {
  return (
    <Stack
      screenOptions={{ headerShown: false }}
      linking={linking} // <-- deep linking setup here
    >
      <Stack.Screen name="index" />
    </Stack>
  );
}





// import { Stack } from 'expo-router';

// export default function RootLayout() {
//   return (
//     <Stack screenOptions={{ headerShown: false }}>
//       <Stack.Screen name="index" />
//     </Stack>
//   );
// }