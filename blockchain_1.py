from __future__ import print_function
import time
import requests
import re
import streamlit as st
import pandas as pd
import numpy as np
import pandas as pd
import docx2txt
import hashlib
import binascii
from merkletools import MerkleTools
import SessionState
import math
import pickle
import base64
import os
import json
import uuid
import datetime
import matplotlib.pyplot as plt
import sendgrid
import os
# from sendgrid.helpers.mail import *

# sg = sendgrid.SendGridAPIClient(api_key="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")


st.set_page_config(layout="wide")


def download_button(object_to_download, download_filename, button_text, pickle_it=False):
    if pickle_it:
        try:
            object_to_download = pickle.dumps(object_to_download)
        except pickle.PicklingError as e:
            st.write(e)
            return None

    else:
        if isinstance(object_to_download, bytes):
            pass

        elif isinstance(object_to_download, pd.DataFrame):
            object_to_download = object_to_download.to_csv(index=False)

        # Try JSON encode for everything else
        else:
            object_to_download = json.dumps(object_to_download)

    try:
        # some strings <-> bytes conversions necessary here
        b64 = base64.b64encode(object_to_download.encode()).decode()

    except AttributeError as e:
        b64 = base64.b64encode(object_to_download).decode()

    button_uuid = str(uuid.uuid4()).replace('-', '')
    button_id = re.sub('\d+', '', button_uuid)

    custom_css = f"""
        <style>
            # {button_id} {{
                background-color: rgb(255, 255, 255);
                color: rgb(38, 39, 48);
                padding: 0.25em 0.38em;
                position: relative;
                text-decoration: none;
                border-radius: 4px;
                border-width: 1px;
                border-style: solid;
                border-color: rgb(230, 234, 241);
                border-image: initial;
            }}
            # {button_id}:hover {{
                border-color: rgb(246, 51, 102);
                color: rgb(246, 51, 102);
            }}
            # {button_id}:active {{
                box-shadow: none;
                background-color: rgb(246, 51, 102);
                color: white;
                }}
        </style> """

    dl_link = custom_css + \
        f'<a download="{download_filename}" id="{button_id}" href="data:file/txt;base64,{b64}">{button_text}</a><br></br>'

    return dl_link


################ Globals ##############

session = SessionState.get(ra='', digest='', proof={}, uploadedProof={}, txnAmount = 0)
fee = 0.00001
receivedTransaction = None
prefix = "444f4350524f4f46"
session.txnAmount = 0.0025

################ Globals ##############
############# Bitcoin Functions #########


def sendTransaction(inputs, digest, address, amount):
    inputString = [{"txid": inputs['txid'], "vout": inputs['vout']}]
    digestString = [{"data": digest}, {address: amount}]
    rawTransaction = host.call(
        'createrawtransaction', inputString, digestString)
    signedTransaction = host.call(
        'signrawtransactionwithwallet', rawTransaction)
    sentTransaction = host.call('sendrawtransaction', signedTransaction['hex'])
    return sentTransaction


def checkForConfirmation(transaction):
    unspent = host.call('listunspent')
    for t in unspent:
        if transaction['txid'] == t['txid']:
            return t
    print("Transaction not yet confirmed")
    # st.write("Transaction not yet confirmed")
    return

def quantityToPrice(quantity):
    y = (1 + math.log(quantity,2)) * 0.0025
    return y


def poe(receiveAddress, digest):
    transactions = host.call('listtransactions')
    # Variable to check received
    received = False

    for transaction in transactions:
        if transaction['category'] == "receive":
            if (transaction['address'] == receiveAddress):
                # Now we check for if the money is greater than the required amount or not
                if (transaction['amount'] >= session.txnAmount):
                    # print("Waiting for confirmation")
                    # st.write("Waiting for confirmation")
                    with st.spinner('Wait for it...'):
                        received = True
                    st.success("Money received. Waiting for block confirmation. Please do not close the window.")
                    receivedTransaction = transaction
                else:
                    received = False
                    st.write("Not enough money received.")
                break

    if not received:
        # Show error
        print("Money not received")
        st.markdown(f"Digest ```{session.digest}```")
        st.markdown(f"Money not received. Pay ```{session.txnAmount}``` BTC at ```{session.ra}```")
    else:
        ticks = 0
        my_bar = st.progress(0)
        
        while True:
            tx = checkForConfirmation(receivedTransaction)
            if tx:
                # Transaction confirmed
                print("Transaction confirmed")
                my_bar.progress(100)
                st.write("Money successfully received with block confirmation. Please download the document proof and keep it safely. You need this to verify your uploaded docuemnts")
                changeAddress = host.call('getrawchangeaddress')
                am = tx['amount'] - fee
                print(am)
                document = prefix + digest
                sentTransaction = sendTransaction(
                    tx, document, changeAddress, round(am, 7))
                st.markdown(f"TxID ```{sentTransaction}```")
                
                session.proof['txid'] = sentTransaction

                download_button_str = download_button(
                    session.proof, "docProof", f'Click here to download', pickle_it=True)

                st.markdown(download_button_str, unsafe_allow_html=True)
                # if st.button("Check transaction on ledger ->"):
                st.write("You can use the above TxiD to check your transaction on the ledger")

                print(sentTransaction)
                break
            else:
                # Transaction not confirmed. Wait for 1 min
                if ticks == 12:
                    st.info("The confirmation is taking some time, please be patient and do not close the window.")
                    time.sleep(10)
                    my_bar.progress(ticks + 10)
                    ticks += 1
                    # email_id = st.text_input("Enter email id")
                    # if(st.button("Send")):
                    #     # Connect to server
                    #     from_email = Email("support@qro.co.in")
                    #     to_email = To(email_id) # Change the input
                    #     subject = "We have received your money successfully"
                    #     content = Content("text/plain", "We have received your money successfully")
                    #     mail = Mail(from_email, to_email, subject, content)
                    #     response = sg.client.mail.send.post(request_body=mail.get())
                    #     print(response.status_code)
                    #     print(response.body)
                    #     print(response.headers)

                elif ticks == 60:
                    print("Breaking the loop. 10 min passed. No money received")
                    st.write("10 min passed. No money received. Please try again or check your exchnage. If any money deducted will be reverted back within 6-9 business days")
                    break
                else:
                    time.sleep(10)
                    my_bar.progress(ticks + 10)
                    ticks += 1
                    
############# Bitcoin Functions #########
############# Merkle Root #########


def merkleRoot(hashDocList, docNumber):
    mt = MerkleTools()
    mt.add_leaf(hashDocList)
    mt.make_tree()
    root = mt.get_merkle_root()
    print(f"M tree root: {root}")

    documentProof = {}
    for i in range(docNumber):
        proof = mt.get_proof(i)
        documentProof[hashDocList[i]] = proof
    session.proof = documentProof
    return root, documentProof
############# Merkle Root #########

############ Connection #################################


class RPCHost(object):
    def __init__(self, url):
        self._session = requests.Session()
        self._url = url
        self._headers = {'content-type': 'application/json'}

    def call(self, rpcMethod, *params):
        payload = json.dumps(
            {"method": rpcMethod, "params": list(params), "jsonrpc": "2.0"})
        tries = 5
        hadConnectionFailures = False
        while True:
            try:
                response = self._session.post(
                    self._url, headers=self._headers, data=payload)
            except requests.exceptions.ConnectionError:
                tries -= 1
                if tries == 0:
                    raise Exception(
                        'Failed to connect for remote procedure call.')
                hadFailedConnections = True
                print("Couldn't connect for remote procedure call, will sleep for five seconds and then try again ({} more tries)".format(tries))
                time.sleep(10)
            else:
                if hadConnectionFailures:
                    print('Connected for remote procedure call after retry.')
                break
        if not response.status_code in (200, 500):
            raise Exception('RPC connection failure: ' +
                            str(response.status_code) + ' ' + response.reason)
        responseJSON = response.json()
        if 'error' in responseJSON and responseJSON['error'] != None:
            # raise Exception('Error in RPC call: ' + str(responseJSON['error']))
            if (rpcMethod == 'getrawtransaction'):
                st.error('Error in transaction id. Please provide the correct details')
                st.stop()
            else:
                st.error("Some error has occured, please retry")
                st.stop()
                # raise Exception('Error in RPC call: ' + str(responseJSON['error']))
                # print('Error in RPC call: ' + str(responseJSON['error']))
            st.stop()
        return responseJSON['result']

# Default port for the bitcoin testnet is 18332
# The port number depends on the one writtein the bitcoin.conf file
rpcPort = 18332
# The RPC username and RPC password MUST match the one in your bitcoin.conf file
rpcUser = 'bitcoin'
rpcPassword = 'kuchbhidaalo'
# Accessing the RPC local server
serverURL = 'http://' + rpcUser + ':' + \
    rpcPassword + '@127.0.0.1:18332'
# Using the class defined in the bitcoin_rpc_class.py
host = RPCHost(serverURL)

# print(host.call('getblockchaininfo'))


################### Connection ###########################
################## Main Setup #############

# st.title('BitNFT')
st.text("\n\n")
with st.beta_container():
    st.markdown("<h1 style='text-align: center; color: white;'>BitNFT</h1>",
                unsafe_allow_html=True)
with st.beta_container():
    # st.markdown("<h3 style='text-align: center; color: white;'>Info</h3>",unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: white;font:Courier New;'>An online medium to allow hassle-free certification of files on the BTC Testnet. You can upload multiple documents, which can individually be verified. </p>",unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: white;font:Courier New;'>A unique feature for this proofofexistence is that a dynamic pricing model is incorporated such that, with more documents, the increase in price per document will be less. The formula for dynamic pricing is as follows where x represents the number of documents. <code> (1 + log_2(x)) * 0.0025) </code></p> ",unsafe_allow_html=True)
    data = {'Documents' : [1,2,3,4,5,6,7,8,9,10], 'Fee': [0.0025,0.005,0.0065,0.0075,0.0083,0.009,0.0095,0.01,0.0104,0.0108]}
    

col1, col2, col3 = st.beta_columns((2,2,1))
with col2:
    df = pd.DataFrame(data, columns = ['Documents', 'Fee'])
    # df.reset_index(drop=True, inplace=True)
    st.dataframe(df, 250, 120)
    st.write("Scroll to see more prices")
st.markdown('''---''')
st.text("\n\n")

col1, col2 = st.beta_columns(2)
st.text("\n\n")

with col1:
    st.subheader('Document Certification')
    st.text("\n\n") 
    st.write('A proof shall be generated using a merkle tree which can be used to verify any of the uploaded documents.')
    s = '[Read More](https://en.wikipedia.org/wiki/Merkle_tree)'
    st.markdown(s, unsafe_allow_html=True)
    st.write('After you upload the docuemnts, you will be required to pay a small fee based on the no. of documents, which is necessary for a blockchain transaction.')
    st.write('You can upload multiple documents. Continue to click on Browse Files')

    uploaded_file = st.file_uploader(
        "Upload your file(s)", accept_multiple_files=True, type=['txt', 'docx', 'pdf'])
    if uploaded_file:
        st.write("CLick process to create a single digest of all your documents.")
        if st.button("Process"):
            hashDoc = []
            session.txnAmount = round(quantityToPrice(len(uploaded_file)),4)
            # st.write(session.txnAmount)
            for i in uploaded_file:
                docx_file = i
                if docx_file.type == "text/plain":
                    raw_text = docx_file.read()

                elif docx_file.type == "application/pdf":
                    raw_text = docx_file.read()

                elif docx_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    raw_text = docx2txt.process(docx_file)

                hex_string = (hashlib.sha256(raw_text)).hexdigest()
                hashDoc.append(hex_string)

            documentsNumber = len(hashDoc)
            treeLength = math.ceil(math.log(documentsNumber, 2))
            toAppend = hashDoc[-1]
            for d in range(documentsNumber, (2**treeLength)):
                hashDoc.append(toAppend)

            print(hashDoc)
            root, proofs = merkleRoot(hashDoc, documentsNumber)
            session.digest = root
            st.markdown(f"Digest ```{root}```")

            # Show address to Pay
            receiveAddress = host.call('getnewaddress')
            # receiveAddress = "tb1q9rhv2g5ku4k0g8rpfgelewsz5ms56y03x42vd3"     # Test Address
            session.ra = receiveAddress
            st.markdown(f"Pay ```{session.txnAmount}``` BTC at ```{session.ra}```")
            # st.write("Pay ", session.txnAmount ," BTC at", session.ra)

    if uploaded_file != None:
        st.write("To complete the process, please pay below")
        if st.button("I have Paid. Proceed to Certify"):
            poe(session.ra, session.digest)
    ################## Main Setup #############
with col2:

    ################# Verification #################
    st.subheader("Verification")
    st.text('\n')

    uploaded_proof = st.file_uploader(
        "Upload your Proof", accept_multiple_files=False)

    if uploaded_proof:
        if uploaded_proof:
            if uploaded_proof.type != "application/octet-stream":
                st.error("Incorrect proof file")
                st.stop()
            # st.write(uploaded_proof.type)
            upProof = pickle.loads(uploaded_proof.read())
            txid = upProof["txid"]
            st.markdown(f"TxiD: ```{txid}```")

    uploadedDocumentToProve = st.file_uploader(
        "Upload your Document (Upload a single document to verify)", accept_multiple_files=False, type=['txt', 'docx', 'pdf'])
    

    if st.button("Verify"):
        if uploaded_proof:
            if uploaded_proof.type != "application/octet-stream":
                st.error("Incorrect proof file")
                st.stop()
            # st.write(uploaded_proof.type)
            upProof = pickle.loads(uploaded_proof.read())
            session.uploadedProof = upProof
            # st.write("TxiD: " + session.uploadedProof["txid"])
        if uploadedDocumentToProve:
            if uploadedDocumentToProve.type == "text/plain":
                raw_text = uploadedDocumentToProve.read()

            elif uploadedDocumentToProve.type == "application/pdf":
                raw_text = uploadedDocumentToProve.read()

            elif uploadedDocumentToProve.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                raw_text = docx2txt.process(uploadedDocumentToProve)

            hex_string = (hashlib.sha256(raw_text)).hexdigest()   # Document Hash

        if uploaded_proof and uploadedDocumentToProve:
            st.write("All files successfully uploaded!")
        else:
            st.error("Error! Not all files have been uploaded succesfully. Please re-upload")
            st.stop()

        rawTxn = host.call("getrawtransaction", session.uploadedProof["txid"])
        decodedTxn = host.call("decoderawtransaction", rawTxn)
        root = decodedTxn["vout"][0]["scriptPubKey"]["hex"][20:]

        mt = MerkleTools()
        key = 0
        for key, val in upProof.items():  # found doc's hash
            if key == hex_string:
                break
        
        if(key == "txid"):
            st.error("The files cound not be verified")
        else:
            result = mt.validate_proof(upProof[key], hex_string, root)
            if (result):
                st.success("Your file has been verified.")
                st.balloons()
            else:
                st.error("The files cound not be verified")

    ################# Verification #################

st.markdown('''---''')
st.subheader("Check you transaction on ledger")
st.write("The OP_RETURN scriptPubKey in the vout section (If exists) is your document digest if you have used proofofexistence.")
txidToVerify = st.text_input("Enter transaction Id")

if txidToVerify != "":
    rawtxn = host.call("getrawtransaction", txidToVerify)
    transaction = host.call("decoderawtransaction", rawtxn)

    st.write(transaction)




# Mention total number of transaction in the output
# Add more attributes. 
# Make the website a little more informative. 
# There are only 2 kind of transaction, segwit and regular
# Multsig, and op_return are type of output (lockscripts)
