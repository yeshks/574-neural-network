import numpy as np
from scipy.optimize import minimize
from scipy.io import loadmat
from math import sqrt
import time
import pickle

f = open("params.pickle", "wb")
dict = {}
def initializeWeights(n_in, n_out):
    """
    # initializeWeights return the random weights for Neural Network given the
    # number of node in the input layer and output layer

    # Input:
    # n_in: number of nodes of the input layer
    # n_out: number of nodes of the output layer
       
    # Output: 
    # W: matrix of random initial weights with size (n_out x (n_in + 1))"""

    epsilon = sqrt(6) / sqrt(n_in + n_out + 1)
    W = (np.random.rand(n_out, n_in + 1) * 2 * epsilon) - epsilon
    return W


def sigmoid(z):
    """# Notice that z can be a scalar, a vector or a matrix
    # return the sigmoid of input z"""
    # z = np.array(z)
    return  1 / (1 + np.exp(-1 * z)) # your code here


def preprocess():
    """ Input:
     Although this function doesn't have any input, you are required to load
     the MNIST data set from file 'mnist_all.mat'.

     Output:
     train_data: matrix of training set. Each row of train_data contains 
       feature vector of a image
     train_label: vector of label corresponding to each image in the training
       set
     validation_data: matrix of training set. Each row of validation_data 
       contains feature vector of a image
     validation_label: vector of label corresponding to each image in the 
       training set
     test_data: matrix of training set. Each row of test_data contains 
       feature vector of a image
     test_label: vector of label corresponding to each image in the testing
       set

     Some suggestions for preprocessing step:
     - feature selection"""

    mat = loadmat('mnist_all.mat')  # loads the MAT object as a Dictionary

    # Pick a reasonable size for validation data

    # ------------Initialize preprocess arrays----------------------#
    train_preprocess = np.zeros(shape=(50000, 784))
    validation_preprocess = np.zeros(shape=(10000, 784))
    test_preprocess = np.zeros(shape=(10000, 784))
    train_label_preprocess = np.zeros(shape=(50000,))
    validation_label_preprocess = np.zeros(shape=(10000,))
    test_label_preprocess = np.zeros(shape=(10000,))
    # ------------Initialize flag variables----------------------#
    train_len = 0
    validation_len = 0
    test_len = 0
    train_label_len = 0
    validation_label_len = 0
    # ------------Start to split the data set into 6 arrays-----------#
    for key in mat:
        # -----------when the set is training set--------------------#
        if "train" in key:
            label = key[-1]  # record the corresponding label
            tup = mat.get(key)
            sap = range(tup.shape[0])
            tup_perm = np.random.permutation(sap)
            tup_len = len(tup)  # get the length of current training set
            tag_len = tup_len - 1000  # defines the number of examples which will be added into the training set

            # ---------------------adding data to training set-------------------------#
            train_preprocess[train_len:train_len + tag_len] = tup[tup_perm[1000:], :]
            train_len += tag_len

            train_label_preprocess[train_label_len:train_label_len + tag_len] = label
            train_label_len += tag_len

            # ---------------------adding data to validation set-------------------------#
            validation_preprocess[validation_len:validation_len + 1000] = tup[tup_perm[0:1000], :]
            validation_len += 1000

            validation_label_preprocess[validation_label_len:validation_label_len + 1000] = label
            validation_label_len += 1000

            # ---------------------adding data to test set-------------------------#
        elif "test" in key:
            label = key[-1]
            tup = mat.get(key)
            sap = range(tup.shape[0])
            tup_perm = np.random.permutation(sap)
            tup_len = len(tup)
            test_label_preprocess[test_len:test_len + tup_len] = label
            test_preprocess[test_len:test_len + tup_len] = tup[tup_perm]
            test_len += tup_len
            # ---------------------Shuffle,double and normalize-------------------------#
    train_size = range(train_preprocess.shape[0])
    train_perm = np.random.permutation(train_size)
    train_data = train_preprocess[train_perm]
    train_data = np.double(train_data)
    train_data = train_data / 255.0
    train_label = train_label_preprocess[train_perm]

    validation_size = range(validation_preprocess.shape[0])
    vali_perm = np.random.permutation(validation_size)
    validation_data = validation_preprocess[vali_perm]
    validation_data = np.double(validation_data)
    validation_data = validation_data / 255.0
    validation_label = validation_label_preprocess[vali_perm]

    test_size = range(test_preprocess.shape[0])
    test_perm = np.random.permutation(test_size)
    test_data = test_preprocess[test_perm]
    test_data = np.double(test_data)
    test_data = test_data / 255.0
    test_label = test_label_preprocess[test_perm]

    # Feature selection
    # Your code here.
    # Remove uninformative attributes

    uninformative_row = np.all(train_data == train_data[0,:], axis=0)
    uninformative_column = np.where(uninformative_row)

    # Get the columns that do not contribute to the network
    # print(uninformative_column)
    selected_features = np.where(uninformative_row == False)[0]
    dict['selected_features'] = selected_features
    # pickle.dump(selected_features, f)
    train_data = np.delete(train_data, uninformative_column, axis=1)
    test_data = np.delete(test_data, uninformative_column, axis=1)
    validation_data = np.delete(validation_data, uninformative_column, axis=1)

    print('Preprocess done')

    return train_data, train_label, validation_data, validation_label, test_data, test_label


def nnObjFunction(params, *args):
    """% nnObjFunction computes the value of objective function (negative log 
    %   likelihood error function with regularization) given the parameters 
    %   of Neural Networks, the training data, their corresponding training
    %   labels and lambda - regularization hyper-parameter.

    % Input:
    % params: vector of weights of 2 matrices w1 (weights of connections from
    %     input layer to hidden layer) and w2 (weights of connections from
    %     hidden layer to output layer) where all of the weights are contained
    %     in a single vector.
    % n_input: number of node in input layer (not include the bias node)
    % n_hidden: number of node in hidden layer (not include the bias node)
    % n_class: number of node in output layer (number of classes in
    %     classification problem
    % training_data: matrix of training data. Each row of this matrix
    %     represents the feature vector of a particular image
    % training_label: the vector of truth label of training images. Each entry
    %     in the vector represents the truth label of its corresponding image.
    % lambda: regularization hyper-parameter. This value is used for fixing the
    %     overfitting problem.
       
    % Output: 
    % obj_val: a scalar value representing value of error function
    % obj_grad: a SINGLE vector of gradient value of error function
    % NOTE: how to compute obj_grad
    % Use backpropagation algorithm to compute the gradient of error function
    % for each weights in weight matrices.

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % reshape 'params' vector into 2 matrices of weight w1 and w2
    % w1: matrix of weights of connections from input layer to hidden layers.
    %     w1(i, j) represents the weight of connection from unit j in input 
    %     layer to unit i in hidden layer.
    % w2: matrix of weights of connections from hidden layer to output layers.
    %     w2(i, j) represents the weight of connection from unit j in hidden 
    %     layer to unit i in output layer."""

    n_input, n_hidden, n_class, training_data, training_label, lambdaval = args

    w1 = params[0:n_hidden * (n_input + 1)].reshape((n_hidden, (n_input + 1)))
    w2 = params[(n_hidden * (n_input + 1)):].reshape((n_class, (n_hidden + 1)))
    obj_val = 0

    # Your Code Here
    pad = np.ones(shape=(len(training_data),1))
    # print(np.shape(training_data))
    training_data = np.concatenate((training_data, pad), axis=1)
    # print(np.shape(training_data))
    summ1 = training_data.dot(w1.T)
    output_1 = sigmoid(summ1) # Hidden layer Output
    # print(np.shape(output_1))

    sig_pad = np.ones(shape=(len(output_1),1))
    output_1 = np.concatenate((output_1, sig_pad), axis=1)
    summ_2 = output_1.dot(w2.T)
    output_2 = sigmoid(summ_2)
    # print(np.shape(output_2))

    outputclass = np.zeros(np.shape(output_2))
    # print(np.shape(outputclass))
    # print(np.shape(training_label))
    for i in range(len(outputclass)):
        for j in range(np.shape(outputclass)[1]):
            if j == int(training_label[i]):
                outputclass[i][j] = 1

    #-------------------------------------------------------
    # Error function calculation

    first_term = outputclass * np.log(output_2)
    second_term = (1 - outputclass) * np.log(1 - output_2)
    third_term = first_term + second_term

    obj_val = (-1/len(training_data)) * np.sum(third_term)

    #-------------------------------------------------------
    # Regularization
    constant = lambdaval / (2*len(training_data))
    first_term = np.sum(np.square(w1), axis=1)
    second_term = np.sum(np.square(w2), axis=1)
    final_term = np.sum(first_term, axis=0)+np.sum(second_term, axis=0)
    obj_val = obj_val + (constant * final_term)

    #-------------------------------------------------------
    # Calculate Gradient

    gradient_w2 = np.zeros(w2.shape)

    gradient_w1 = np.zeros(w1.shape)
    delta = np.subtract(output_2, outputclass)

    gradient_w2 = (1/len(training_data)) * (delta.T).dot(output_1)
    # print(gradient_w2.shape)
    gradient_w2 = gradient_w2 + ((lambdaval*w2)/len(training_data))

    mult = (1 - output_1[:,:n_hidden])*output_1[:,:n_hidden]
    delta = delta.dot(w2[:,:n_hidden])
    mult = mult * delta

    gradient_w1 = (1/len(training_data))*((mult.T).dot(training_data))
    gradient_w1 = gradient_w1 + (lambdaval*w1/len(training_data))

    obj_grad = np.concatenate((gradient_w1.flatten(), gradient_w2.flatten()),0)

    return (obj_val, obj_grad)


def nnPredict(w1, w2, data):
    """% nnPredict predicts the label of data given the parameter w1, w2 of Neural
    % Network.

    % Input:
    % w1: matrix of weights of connections from input layer to hidden layers.
    %     w1(i, j) represents the weight of connection from unit i in input 
    %     layer to unit j in hidden layer.
    % w2: matrix of weights of connections from hidden layer to output layers.
    %     w2(i, j) represents the weight of connection from unit i in input 
    %     layer to unit j in hidden layer.
    % data: matrix of data. Each row of this matrix represents the feature 
    %       vector of a particular image
       
    % Output: 
    % label: a column vector of predicted labels"""

    labels = np.array([])
    # Your code here

    data = np.concatenate((data, np.ones(shape=(len(data),1))), axis=1)
    summ = data.dot(w1.T)
    output = sigmoid(summ)
    output = np.concatenate((output, np.ones(shape=(len(output), 1))), axis=1)
    summ2 = output.dot(w2.T)
    output_2 = sigmoid(summ2)

    labels = np.argmax(output_2, axis=1)

    return labels


"""**************Neural Network Script Starts here********************************"""

now = time.time()

train_data, train_label, validation_data, validation_label, test_data, test_label = preprocess()

#  Train Neural Network

# set the number of nodes in input unit (not including bias unit)
n_input = train_data.shape[1]

# set the number of nodes in hidden unit (not including bias unit)
n_hidden = 50

# set the number of nodes in output unit
n_class = 10

# initialize the weights into some random matrices
initial_w1 = initializeWeights(n_input, n_hidden)
initial_w2 = initializeWeights(n_hidden, n_class)

# unroll 2 weight matrices into single column vector
initialWeights = np.concatenate((initial_w1.flatten(), initial_w2.flatten()), 0)

# set the regularization hyper-parameter
lambdaval = 5

args = (n_input, n_hidden, n_class, train_data, train_label, lambdaval)

# Train Neural Network using fmin_cg or minimize from scipy,optimize module. Check documentation for a working example

opts = {'maxiter': 50}  # Preferred value.

nn_params = minimize(nnObjFunction, initialWeights, jac=True, args=args, method='CG', options=opts)
print("Time to train", time.time()-now,"seconds")
# In Case you want to use fmin_cg, you may have to split the nnObjectFunction to two functions nnObjFunctionVal
# and nnObjGradient. Check documentation for this function before you proceed.
# nn_params, cost = fmin_cg(nnObjFunctionVal, initialWeights, nnObjGradient,args = args, maxiter = 50)


# Reshape nnParams from 1D vector into w1 and w2 matrices
w1 = nn_params.x[0:n_hidden * (n_input + 1)].reshape((n_hidden, (n_input + 1)))
w2 = nn_params.x[(n_hidden * (n_input + 1)):].reshape((n_class, (n_hidden + 1)))

# Test the computed parameters

predicted_label = nnPredict(w1, w2, train_data)
# find the accuracy on Training Dataset
print('\nTraining set Accuracy:' + str(100 * np.mean((predicted_label == train_label).astype(float))) + '%')

predicted_label = nnPredict(w1, w2, validation_data)
# find the accuracy on Validation Dataset
print('\nValidation set Accuracy:' + str(100 * np.mean((predicted_label == validation_label).astype(float))) + '%')

predicted_label = nnPredict(w1, w2, test_data)
# find the accuracy on test Dataset
print('\nTest set Accuracy:' + str(100 * np.mean((predicted_label == test_label).astype(float))) + '%')

dict['n_hidden'] = n_hidden
dict['w1'] = w1
dict['w2'] = w2
dict['lambdaval'] = lambdaval
pickle.dump(n_hidden, f)
pickle.dump(w1, f)
pickle.dump(w2, f)
pickle.dump(lambdaval, f)
f.close()