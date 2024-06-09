import { useState } from 'react'
import MlInstance from '../Api/mlapi';
import './index.css'

const SubmitLink = () => {
    const [varLink, setVarLink] = useState('');

    const FnLinkChanged = e => {
        setVarLink(e.target.value);
    }

    const FnLinkSubmitted = async (e) => {
        e.preventDefault();
        try {
            const response = await MlInstance.post('/youtube_url', { youtube_url: varLink });
            console.log('Response:', response.data); // Handle the response
        } catch (error) {
            console.error('There was an error making the request:', error); // Handle errors
        }
    };
      
    return (
        <div className='submit-link-container'>
            <h1 className='you-quiz-heading'>You-Quiz</h1>
            <form className='form' onSubmit={FnLinkSubmitted}>
                <input type='text' value={varLink} onChange={FnLinkChanged} className='link-input' placeholder='paste your link here' />
                <button type='submit' className='generate-btn'>Generate</button>
            </form>
        </div>
    )
}

export default SubmitLink