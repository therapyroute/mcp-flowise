import unittest
import os
from mcp_flowise.utils import flowise_predict

class TestToolPrediction(unittest.TestCase):
    """
    Integration test for predicting results from a Flowise chatflow.
    """

    def test_tool_prediction(self):
        """
        Test the prediction function for a Flowise chatflow.
        """
        # Check if FLOWISE_CHATFLOW_ID is set
        chatflow_id = os.getenv("FLOWISE_CHATFLOW_ID")
        if not chatflow_id:
            self.skipTest("FLOWISE_CHATFLOW_ID environment variable is not set.")
        
        question = "What is the weather like today?"
        print(f"Using chatflow_id: {chatflow_id}")
        
        # Make a prediction
        result = flowise_predict(chatflow_id, question)
        
        # Validate the response
        self.assertIsInstance(result, str)
        self.assertNotEqual(result.strip(), "", "Prediction result should not be empty.")
        print(f"Prediction result: {result}")

if __name__ == "__main__":
    unittest.main()
