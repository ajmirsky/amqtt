import './App.css'

import { alpha } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';

import AppTheme from './shared-theme/AppTheme';
import AmqttLogo from './dashboard/amqtt_bw.svg';

import AppBar from "@mui/material/AppBar";
import {Toolbar} from "@mui/material";
import UserManager from "./dashboard/UserManager.tsx";
import SignIn from "./login/SignIn.tsx";

const xThemeComponents = {};

function App(props: { disableCustomTheme?: boolean }) {
  return (
    <AppTheme {...props} themeComponents={xThemeComponents}>
      <CssBaseline enableColorScheme />
      <AppBar position="static" elevation={6}>
        <Toolbar style={{minWidth:800}}>
          <img
            src={AmqttLogo}
            style={{width: 150}}
            alt="website logo"
          />

        </Toolbar>
      </AppBar>
      <Box sx={{display: 'flex', width:'100%'}}>
        < SignIn />
      </Box>
    </AppTheme>
  );
}

export default App;