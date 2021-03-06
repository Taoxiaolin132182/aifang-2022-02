import tensorflow as tf
from tensorflow.python.ops import array_ops


def focal_loss(prediction_tensor, target_tensor, weights=None, alpha=0.25, gamma=2):
    r"""Compute focal loss for predictions.
        Multi-labels Focal loss formula:
            FL = -alpha * (z-p)^gamma * log(p) -(1-alpha) * p^gamma * log(1-p)
                 ,which alpha = 0.25, gamma = 2, p = sigmoid(x), z = target_tensor.
    Args:
     prediction_tensor: A float tensor of shape [batch_size, num_anchors,
        num_classes] representing the predicted logits for each class
     target_tensor: A float tensor of shape [batch_size, num_anchors,
        num_classes] representing one-hot encoded classification targets
     weights: A float tensor of shape [batch_size, num_anchors]
     alpha: A scalar tensor for focal loss alpha hyper-parameter
     gamma: A scalar tensor for focal loss gamma hyper-parameter
    Returns:
        loss: A (scalar) tensor representing the value of the loss function
    """
    sigmoid_p = tf.nn.sigmoid(prediction_tensor)
    zeros = array_ops.zeros_like(sigmoid_p, dtype=sigmoid_p.dtype)

    # For poitive prediction, only need consider front part loss, back part is 0;
    # target_tensor > zeros <=> z=1, so poitive coefficient = z - p.
    pos_p_sub = array_ops.where(target_tensor > zeros, target_tensor - sigmoid_p, zeros)

    # For negative prediction, only need consider back part loss, front part is 0;
    # target_tensor > zeros <=> z=1, so negative coefficient = 0.
    neg_p_sub = array_ops.where(target_tensor > zeros, zeros, sigmoid_p)
    per_entry_cross_ent = - alpha * (pos_p_sub ** gamma) * tf.log(tf.clip_by_value(sigmoid_p, 1e-8, 1.0)) \
                          - (1 - alpha) * (neg_p_sub ** gamma) * tf.log(tf.clip_by_value(1.0 - sigmoid_p, 1e-8, 1.0))
    # return tf.reduce_sum(per_entry_cross_ent)
    return per_entry_cross_ent

def multi_category_focal_loss1(y_true, y_pred):
    y_pred = tf.nn.sigmoid(y_pred)
    y_true = tf.reshape(y_true, [-1, 2])
    y_pred = tf.reshape(y_pred, [-1, 2])
    epsilon = 1.e-7
    gamma = 2.0
    # alpha = tf.constant([[2],[1],[1],[1],[1]], dtype=tf.float32)
    alpha = tf.constant([[1], [9]], dtype=tf.float32)

    y_true = tf.cast(y_true, tf.float32)
    y_pred = tf.clip_by_value(y_pred, epsilon, 1. - epsilon)
    y_t = tf.multiply(y_true, y_pred) + tf.multiply(1-y_true, 1-y_pred)
    ce = -tf.log(y_t)
    weight = tf.pow(tf.subtract(1., y_t), gamma)
    loss = tf.matmul(tf.multiply(weight, ce), alpha)
    # loss = tf.reduce_mean(fl)
    return loss

# def multi_category_focal_loss2_fixed(y_true, y_pred):
#     epsilon = 1.e-7
#     gamma=2.
#     alpha = tf.constant(0.5, dtype=tf.float32)
#
#     y_true = tf.cast(y_true, tf.float32)
#     y_pred = tf.clip_by_value(y_pred, epsilon, 1. - epsilon)
#
#     alpha_t = y_true*alpha + (tf.ones_like(y_true)-y_true)*(1-alpha)
#     y_t = tf.multiply(y_true, y_pred) + tf.multiply(1-y_true, 1-y_pred)
#     ce = -tf.log(y_t)
#     weight = tf.pow(tf.subtract(1., y_t), gamma)
#     loss = tf.multiply(tf.multiply(weight, ce), alpha_t)
#     # loss = tf.reduce_mean(fl)
#     return loss


# def binary_focal_loss(gamma=2, alpha=0.25):
#     """
#     Binary form of focal loss.
#     ???????????????????????????focal loss
#
#     focal_loss(p_t) = -alpha_t * (1 - p_t)**gamma * log(p_t)
#         where p = sigmoid(x), p_t = p or 1 - p depending on if the label is 1 or 0, respectively.
#     References:
#         https://arxiv.org/pdf/1708.02002.pdf
#     Usage:
#      model.compile(loss=[binary_focal_loss(alpha=.25, gamma=2)], metrics=["accuracy"], optimizer=adam)
#     """
#     alpha = tf.constant(alpha, dtype=tf.float32)
#     gamma = tf.constant(gamma, dtype=tf.float32)
#
#     def binary_focal_loss_fixed(y_true, y_pred):
#         """
#         y_true shape need be (None,1)
#         y_pred need be compute after sigmoid
#         """
#         y_true = tf.cast(y_true, tf.float32)
#         alpha_t = y_true * alpha + (K.ones_like(y_true) - y_true) * (1 - alpha)
#
#         p_t = y_true * y_pred + (K.ones_like(y_true) - y_true) * (K.ones_like(y_true) - y_pred) + K.epsilon()
#         focal_loss = - alpha_t * K.pow((K.ones_like(y_true) - p_t), gamma) * K.log(p_t)
#         return K.mean(focal_loss)
#
#     return binary_focal_loss_fixed
#
#
# def multi_category_focal_loss1_(alpha, gamma=2.0):
#     """
#     focal loss for multi category of multi label problem
#     ???????????????????????????????????????focal loss
#     alpha????????????????????????/?????????????????????????????????????????????????????????
#     ??????????????????????????????/????????????????????????????????????????????????????????????loss
#     Usage:
#      model.compile(loss=[multi_category_focal_loss1(alpha=[1,2,3,2], gamma=2)], metrics=["accuracy"], optimizer=adam)
#     """
#     epsilon = 1.e-7
#     alpha = tf.constant(alpha, dtype=tf.float32)
#     # alpha = tf.constant([[1],[1],[1],[1],[1]], dtype=tf.float32)
#     # alpha = tf.constant_initializer(alpha)
#     gamma = float(gamma)
#
#     def multi_category_focal_loss1_fixed(y_true, y_pred):
#         y_true = tf.cast(y_true, tf.float32)
#         y_pred = tf.clip_by_value(y_pred, epsilon, 1. - epsilon)
#         y_t = tf.multiply(y_true, y_pred) + tf.multiply(1 - y_true, 1 - y_pred)
#         ce = -tf.log(y_t)
#         weight = tf.pow(tf.subtract(1., y_t), gamma)
#         fl = tf.matmul(tf.multiply(weight, ce), alpha)
#         loss = tf.reduce_mean(fl)
#         return loss
#
#     return multi_category_focal_loss1_fixed
#
#
# def multi_category_focal_loss2(gamma=2., alpha=.25):
#     """
#     focal loss for multi category of multi label problem
#     ???????????????????????????????????????focal loss
#     alpha????????????y_true???1/0????????????
#         1????????????alpha, 0????????????1-alpha
#     ????????????????????????????????????????????????????????????????????????????????????loss
#     ?????????????????????(????????????????????????????????????1),?????????alpha??????
#     ?????????????????????(????????????????????????????????????0,??????????????????????????????,??????????????????????????????)
#         ?????????alpha??????,???????????????????????????1???
#     Usage:
#      model.compile(loss=[multi_category_focal_loss2(alpha=0.25, gamma=2)], metrics=["accuracy"], optimizer=adam)
#     """
#     epsilon = 1.e-7
#     gamma = float(gamma)
#     alpha = tf.constant(alpha, dtype=tf.float32)
#
#     def multi_category_focal_loss2_fixed(y_true, y_pred):
#         y_true = tf.cast(y_true, tf.float32)
#         y_pred = tf.clip_by_value(y_pred, epsilon, 1. - epsilon)
#
#         alpha_t = y_true * alpha + (tf.ones_like(y_true) - y_true) * (1 - alpha)
#         y_t = tf.multiply(y_true, y_pred) + tf.multiply(1 - y_true, 1 - y_pred)
#         ce = -tf.log(y_t)
#         weight = tf.pow(tf.subtract(1., y_t), gamma)
#         fl = tf.multiply(tf.multiply(weight, ce), alpha_t)
#         loss = tf.reduce_mean(fl)
#         return loss
#
#     return multi_category_focal_loss2_fixed
