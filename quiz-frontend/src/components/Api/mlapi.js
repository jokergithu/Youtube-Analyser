import axios from 'axios';

const apiUrl = 'http://localhost:8080';

const MlInstance = axios.create({
  baseURL: apiUrl,
  headers: {
    'Accept': '*/*',
    'Content-Type': 'application/x-www-form-urlencoded',
  }
});

export default MlInstance;
