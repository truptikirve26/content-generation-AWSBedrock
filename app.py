import boto3
import botocore.config
import json
from botocore.exceptions import ClientError

from datetime import datetime


def generate_blog(blog_topic: str) -> str:
    prompt = f"""<s>[INST]Human: Write a 200 words blog on {blog_topic}.
    Assistant:[/INST]
    """

    body = {
        "prompt": prompt,
        "max_gen_len": 512,
        "temperature": 0.8,
        "top_p": 0.9
    }
    inference_profile_identifier = "arn:aws:bedrock:us-east-2:924483358735:inference-profile/us.meta.llama3-2-1b-instruct-v1:0"
    modelId = "meta.llama3-2-1b-instruct-v1:0"

    try:
        bedrock = boto3.client("bedrock-runtime", region_name="us-east-2",
                               config=botocore.config.Config(read_timeout=300, retries={'max_attempts': 3}))
        response = bedrock.invoke_model(body=json.dumps(body), modelId=inference_profile_identifier)

        response_content = response.get('body').read()
        response_data = json.loads(response_content)
        print(response_data)

        blog_details = response_data['generation']
        return blog_details

    except Exception as e:
        print(f"Error generating the blog: {e}")
        return ""


def save_blog_s3(s3_key, s3_bucket, blog):
    s3 = boto3.client('s3')

    try:
        response = s3.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=blog.encode('utf-8'),
            ContentType='text/plain'
        )

        # Check for a successful response (HTTP status code 200 indicates success)
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print(f"Text content uploaded successfully to s3://{s3_bucket}/{s3_key}")
        else:
            print(f"Failed to upload text content. Response: {response}")

    except ClientError as e:
        print(f"An AWS Client error occurred: {e}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def lambda_handler(event, context):
    event = json.loads(event['body'])
    blog_topic = event['blog_topic']

    blog = generate_blog(blog_topic=blog_topic)

    if blog:
        current_time = datetime.now().strftime('%H%M%S')
        s3_key = f"blog-output/{blog_topic}_{current_time}.txt"
        s3_bucket = 'aws-bedrock-content-generation'
        save_blog_s3(s3_key, s3_bucket, blog)

    else:
        print("Blog is not generated")

    return {
        'statusCode': 200,
        'body': json.dumps('Blog Generated')
    }

