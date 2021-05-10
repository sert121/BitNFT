# BitNFT

An online medium to allow hassle-free certification of files on the BTC Testnet.

## Setup

For setting up a full bitcoin node, please refer [BTC Core](https://bit.ly/3hg2TMy).  
For a video-demo of the setup please refer [[1]](https://drive.google.com/file/d/1FJwqIkqRVJ71aikOYbtEe5acMh3zFg4_/view?usp=sharing)  
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the requirements.
```bash
pip install -r requirements.txt 
```

## Usage
Users can interact with the webapp available at [BitNFT](http://206.189.131.95:8501/).   
To run the project locally : ```streamlit run blockchain_1.py```

### Project Walkthrough

To interact with Bitcoin ledger, we setup a [Json-RPC](https://developer.bitcoin.org/reference/rpc/) Client-Server connection between our web-app and the bitcoin node.  
```class RPCHost()``` helps to intialize a host object to interact with btc-ledger, via json rpc. Handles commonly occuring HTTP-based errors while connecting to btc node, and displays appropriate response codes accordingly.

After successfully connecting with the host, we record user input via the web-app, to allow uploading of documents.  
     After the documents are uploaded, a unique ```address``` is generated which can be used for payment.  
(```doc2text``` is used to check for valid document types uploaded by the user)
  
Once the user uploads their documents, 
we create a transaction which includes the hash of documents with the help of a ```merkletree```. To send a transaction to the ```btc-core``` we use ```sendTransaction()``` which constructs an appropriate dictionary, with transaction details, and sends it via the ```Host``` object. The user is then requested to pay the appropriate fee for the transaction. The payment is checked via ```checkconfirmation()```, and soon as the payment is confirmed a  ```docProof``` is generated using ```poe()```, which can be downloaded via ```download()```. 
  To verify any of the uploaded documents, one can  simply upload their docProof on [BitNFT](http://206.189.131.95:8501/) 
## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/)
