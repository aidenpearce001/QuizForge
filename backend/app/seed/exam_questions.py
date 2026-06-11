"""Seed 35 midterm exam questions (for_exam=True) — bilingual EN/VI from the AWS midterm docx."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Domain
from app.models.question import Question
from app.models.subject import Subject

# question_text format: "English text\n\nVietnamese text"
# choice text format:   "English text\nVietnamese text"
EXAM_QUESTIONS_BY_DOMAIN = {
    "AWS Global Infrastructure & Cloud Economics": [
        {
            "text": "A company provides you with a completed product that is run and managed by the company itself. As a customer, you only use the product without worrying about maintaining or managing the product. Which cloud computing model does this kind of product belong to?\n\nMột công ty cung cấp cho bạn một sản phẩm hoàn chỉnh được vận hành và quản lý bởi chính công ty đó. Với vai trò khách hàng, bạn chỉ sử dụng sản phẩm mà không cần quan tâm đến việc bảo trì hoặc quản lý sản phẩm. Sản phẩm này thuộc mô hình điện toán đám mây nào?",
            "type": "single",
            "choices": [
                {"text": "Platform as a Service (PaaS)\nNền tảng dưới dạng dịch vụ", "is_correct": False},
                {"text": "Infrastructure as a Service (IaaS)\nHạ tầng dưới dạng dịch vụ", "is_correct": False},
                {"text": "Product as a Service (PaaS)\nSản phẩm dưới dạng dịch vụ", "is_correct": False},
                {"text": "Software as a Service (SaaS)\nPhần mềm dưới dạng dịch vụ", "is_correct": True},
            ],
        },
        {
            "text": "Which of the following describes an Availability Zone (AZ) in the AWS Cloud?\n\nPhát biểu nào sau đây mô tả đúng về Availability Zone (AZ) trong AWS Cloud?",
            "type": "single",
            "choices": [
                {"text": "One or more data centers in the same location\nMột hoặc nhiều trung tâm dữ liệu trong cùng một vị trí", "is_correct": True},
                {"text": "One or more server racks in the same location\nMột hoặc nhiều tủ máy chủ trong cùng một vị trí", "is_correct": False},
                {"text": "One or more data centers in multiple locations\nMột hoặc nhiều trung tâm dữ liệu ở nhiều vị trí khác nhau", "is_correct": False},
                {"text": "One or more server racks in multiple locations\nMột hoặc nhiều tủ máy chủ ở nhiều vị trí khác nhau", "is_correct": False},
            ],
        },
        {
            "text": "How can you deploy your EC2 instances so that if a single data center fails you still have instances available?\n\nLàm thế nào để triển khai các EC2 instance nhằm đảm bảo rằng nếu một data center gặp sự cố thì vẫn còn instance hoạt động?",
            "type": "single",
            "choices": [
                {"text": "Across subnets\nTriển khai trên nhiều subnet", "is_correct": False},
                {"text": "Across VPCs\nTriển khai trên nhiều VPC", "is_correct": False},
                {"text": "Across regions\nTriển khai trên nhiều region", "is_correct": False},
                {"text": "Across Availability Zones\nTriển khai trên nhiều Availability Zone", "is_correct": True},
            ],
        },
        {
            "text": "Which of the statements below does NOT characterize cloud computing?\n\nPhát biểu nào dưới đây KHÔNG phải là đặc điểm của cloud computing?",
            "type": "single",
            "choices": [
                {"text": "Cloud computing allows you to swap variable expense for capital expense\nCloud computing cho phép chuyển chi phí biến đổi thành chi phí đầu tư", "is_correct": True},
                {"text": "With cloud computing you get to benefit from massive economies of scale\nCloud computing giúp tận dụng lợi thế kinh tế theo quy mô lớn", "is_correct": False},
                {"text": "Cloud computing is the on-demand delivery of compute power\nCloud computing là việc cung cấp tài nguyên tính toán theo nhu cầu", "is_correct": False},
                {"text": "With cloud computing you can increase your speed and agility\nCloud computing giúp tăng tốc độ và tính linh hoạt", "is_correct": False},
            ],
        },
        {
            "text": "The DevOps team at a Big Data consultancy has set up Amazon EC2 instances across two AWS Regions for its flagship application. Which of the following characterizes this application architecture?\n\nĐội DevOps tại một công ty tư vấn Big Data đã triển khai các Amazon EC2 instance trên hai AWS Region cho ứng dụng chủ lực của họ. Đặc điểm nào sau đây mô tả kiến trúc ứng dụng này?",
            "type": "single",
            "choices": [
                {"text": "Deploying the application across two AWS Regions improves availability\nTriển khai ứng dụng trên hai AWS Region giúp tăng tính sẵn sàng", "is_correct": True},
                {"text": "Deploying the application across two AWS Regions improves security\nTriển khai ứng dụng trên hai AWS Region giúp tăng bảo mật", "is_correct": False},
                {"text": "Deploying the application across two AWS Regions improves scalability\nTriển khai ứng dụng trên hai AWS Region giúp tăng khả năng mở rộng", "is_correct": False},
                {"text": "Deploying the application across two AWS Regions improves agility\nTriển khai ứng dụng trên hai AWS Region giúp tăng tính linh hoạt", "is_correct": False},
            ],
        },
        {
            "text": "Which of the following is the best practice for application architecture on AWS Cloud?\n\nĐâu là best practice cho kiến trúc ứng dụng trên AWS Cloud?",
            "type": "single",
            "choices": [
                {"text": "Build tightly coupled components\nXây dựng các thành phần phụ thuộc chặt chẽ", "is_correct": False},
                {"text": "Build monolithic applications\nXây dựng ứng dụng nguyên khối", "is_correct": False},
                {"text": "Build loosely coupled components\nXây dựng các thành phần liên kết lỏng lẻo", "is_correct": True},
                {"text": "Use synchronous communication between components\nSử dụng giao tiếp đồng bộ giữa các thành phần", "is_correct": False},
            ],
        },
        {
            "text": "Which AWS service can be used to send, store, and receive messages between software components at any volume to decouple application tiers?\n\nDịch vụ AWS nào có thể được sử dụng để gửi, lưu trữ và nhận message giữa các thành phần phần mềm ở bất kỳ quy mô nào nhằm tách biệt các tầng ứng dụng?",
            "type": "single",
            "choices": [
                {"text": "AWS Organizations\nAWS Organizations", "is_correct": False},
                {"text": "Amazon Simple Queue Service (Amazon SQS)\nAmazon Simple Queue Service (Amazon SQS)", "is_correct": True},
                {"text": "Amazon Simple Notification Service (Amazon SNS)\nAmazon Simple Notification Service (Amazon SNS)", "is_correct": False},
                {"text": "AWS Elastic Beanstalk\nAWS Elastic Beanstalk", "is_correct": False},
            ],
        },
        {
            "text": "A company needs to keep sensitive data in its own data center due to compliance but would still like to deploy resources using AWS. Which Cloud deployment model does this refer to?\n\nMột công ty cần lưu trữ dữ liệu nhạy cảm trong data center riêng do yêu cầu tuân thủ nhưng vẫn muốn triển khai tài nguyên bằng AWS. Điều này thuộc mô hình triển khai cloud nào?",
            "type": "single",
            "choices": [
                {"text": "Private Cloud\nCloud riêng", "is_correct": False},
                {"text": "Public Cloud\nCloud công cộng", "is_correct": False},
                {"text": "On-premises\nHạ tầng tại chỗ", "is_correct": False},
                {"text": "Hybrid Cloud\nCloud lai", "is_correct": True},
            ],
        },
        {
            "text": "Which of the following points have to be considered when choosing an AWS Region for a service? (Select two)\n\nNhững yếu tố nào sau đây cần được xem xét khi lựa chọn AWS Region cho một dịch vụ? (Chọn HAI đáp án)",
            "type": "multiple",
            "choices": [
                {"text": "Compliance and Data Residency guidelines of the AWS Region should match your business requirements\nCác hướng dẫn về tuân thủ và lưu trú dữ liệu của AWS Region phải phù hợp với yêu cầu doanh nghiệp của bạn", "is_correct": True},
                {"text": "AWS Region chosen should be geographically closer to the user base that utilizes the hosted AWS services\nAWS Region được chọn nên gần về mặt địa lý với nhóm người dùng sử dụng các dịch vụ AWS được triển khai", "is_correct": True},
                {"text": "The AWS Region should have 5G networks, to seamlessly access the breadth of AWS services in the region\nAWS Region nên có mạng 5G để truy cập đầy đủ các dịch vụ AWS trong region", "is_correct": False},
                {"text": "The AWS Region should have a high availability index for your business\nAWS Region có chỉ số sẵn sàng cao nên được xem xét cho doanh nghiệp", "is_correct": False},
                {"text": "The AWS Region chosen should have all its AZs within 100 Kms radius, to keep latency low\nAWS Region được chọn nên có tất cả AZ trong bán kính 100km để giữ độ trễ thấp", "is_correct": False},
            ],
        },
        {
            "text": "A cargo shipping company runs EC2 instances hosting CRM applications that need 24*7 access but are not mission-critical. In a disaster, they can run on fewer instances temporarily. Which disaster recovery strategy is well-suited and cost-effective?\n\nMột công ty vận tải hàng hóa chạy EC2 instance cho ứng dụng CRM cần truy cập 24/7 nhưng không phải mission-critical. Trong thảm họa, chúng có thể hoạt động với ít instance hơn. Chiến lược disaster recovery nào phù hợp và tiết kiệm chi phí?",
            "type": "single",
            "choices": [
                {"text": "Pilot Light strategy\nChiến lược Pilot Light", "is_correct": False},
                {"text": "Backup & Restore strategy\nChiến lược Backup & Restore", "is_correct": False},
                {"text": "Warm Standby strategy\nChiến lược Warm Standby", "is_correct": True},
                {"text": "Multi-site active-active strategy\nChiến lược Multi-site active-active", "is_correct": False},
            ],
        },
        {
            "text": "Which AWS Cloud design principles can help increase reliability? (Select TWO.)\n\nNhững nguyên tắc thiết kế AWS Cloud nào có thể giúp tăng reliability? (Chọn HAI đáp án)",
            "type": "multiple",
            "choices": [
                {"text": "Using monolithic architecture\nSử dụng kiến trúc monolithic", "is_correct": False},
                {"text": "Automatically recovering from failure\nTự động phục hồi khi có lỗi", "is_correct": True},
                {"text": "Adopting a consumption model\nÁp dụng mô hình tiêu thụ theo nhu cầu", "is_correct": False},
                {"text": "Measuring overall efficiency\nĐo lường hiệu quả tổng thể", "is_correct": False},
                {"text": "Testing recovery procedures\nKiểm thử quy trình phục hồi", "is_correct": True},
            ],
        },
    ],
    "IAM — Identity, Access & Security Fundamentals": [
        {
            "text": "Which AWS service allows you to quickly and easily add user sign-up, sign-in, and access control to web and mobile applications?\n\nDịch vụ AWS nào cho phép bạn nhanh chóng và dễ dàng thêm chức năng đăng ký người dùng, đăng nhập và kiểm soát truy cập cho các ứng dụng web và mobile?",
            "type": "single",
            "choices": [
                {"text": "AWS IAM Identity Center\nAWS IAM Identity Center", "is_correct": False},
                {"text": "Amazon Cognito\nAmazon Cognito", "is_correct": True},
                {"text": "AWS Organizations\nAWS Organizations", "is_correct": False},
                {"text": "AWS Identity and Access Management (AWS IAM)\nAWS Identity and Access Management (AWS IAM)", "is_correct": False},
            ],
        },
        {
            "text": "A financial services enterprise plans to enable Multi-Factor Authentication (MFA) for its employees. For ease of travel, they prefer not to use any physical devices. Which option is best suited?\n\nMột doanh nghiệp dịch vụ tài chính dự định bật MFA cho nhân viên. Để thuận tiện khi di chuyển, họ không muốn sử dụng thiết bị vật lý. Lựa chọn nào phù hợp nhất?",
            "type": "single",
            "choices": [
                {"text": "U2F security key\nKhóa bảo mật U2F", "is_correct": False},
                {"text": "Virtual Multi-Factor Authentication (MFA) device\nThiết bị MFA ảo", "is_correct": True},
                {"text": "Soft Token Multi-Factor Authentication (MFA) device\nThiết bị MFA soft token", "is_correct": False},
                {"text": "Hardware Multi-Factor Authentication (MFA) device\nThiết bị MFA phần cứng", "is_correct": False},
            ],
        },
    ],
    "Core Compute — EC2, Lambda & Containers": [
        {
            "text": "A company is moving its on-premises application to AWS Cloud. The application uses in-memory caches for running custom workloads. Which Amazon EC2 instance type is the right choice?\n\nMột công ty đang chuyển ứng dụng on-premises lên AWS Cloud. Ứng dụng sử dụng in-memory cache để chạy các workload tùy chỉnh. Loại Amazon EC2 instance nào là lựa chọn phù hợp?",
            "type": "single",
            "choices": [
                {"text": "Accelerated computing instance types\nCác loại instance tối ưu tăng tốc phần cứng", "is_correct": False},
                {"text": "Compute Optimized instance types\nCác loại instance tối ưu tính toán", "is_correct": False},
                {"text": "Storage Optimized instance types\nCác loại instance tối ưu lưu trữ", "is_correct": False},
                {"text": "Memory Optimized instance types\nCác loại instance tối ưu bộ nhớ", "is_correct": True},
            ],
        },
        {
            "text": "Which of the following statements is the MOST accurate when describing AWS Elastic Beanstalk?\n\nPhát biểu nào sau đây là CHÍNH XÁC NHẤT khi mô tả AWS Elastic Beanstalk?",
            "type": "single",
            "choices": [
                {"text": "It is an Infrastructure as Code (IaC) that allows you to model and provision resources needed for an application\nĐây là một dịch vụ Infrastructure as Code (IaC) cho phép mô hình hóa và cấp phát tài nguyên cần thiết cho ứng dụng", "is_correct": False},
                {"text": "It is an Infrastructure as a Service (IaaS) that allows you to deploy and scale web applications and services\nĐây là một dịch vụ Infrastructure as a Service (IaaS) cho phép triển khai và mở rộng các ứng dụng web và dịch vụ", "is_correct": False},
                {"text": "It is a Platform as a Service (PaaS) that allows you to model and provision resources needed for an application\nĐây là một dịch vụ Platform as a Service (PaaS) cho phép mô hình hóa và cấp phát tài nguyên cần thiết cho ứng dụng", "is_correct": False},
                {"text": "It is a Platform as a Service (PaaS) that allows you to deploy and scale web applications and services\nĐây là một dịch vụ Platform as a Service (PaaS) cho phép triển khai và mở rộng các ứng dụng web và dịch vụ", "is_correct": True},
            ],
        },
        {
            "text": "A company is looking at a service to automate and minimize the time spent on keeping server images up-to-date. These server images are used by Amazon EC2 instances as well as on-premises systems. Which AWS service will help?\n\nMột công ty đang tìm kiếm một dịch vụ để tự động hóa và giảm thiểu thời gian cập nhật server image dùng cho cả Amazon EC2 và hệ thống on-premises. Dịch vụ AWS nào sẽ giúp đáp ứng nhu cầu này?",
            "type": "single",
            "choices": [
                {"text": "AWS Systems Manager (SSM)\nAWS Systems Manager (SSM)", "is_correct": False},
                {"text": "Amazon EC2 Image Builder\nAmazon EC2 Image Builder", "is_correct": True},
                {"text": "AWS CloudFormation templates\nAWS CloudFormation templates", "is_correct": False},
                {"text": "Amazon EC2 Amazon Machine Image (AMI)\nAmazon EC2 Amazon Machine Image (AMI)", "is_correct": False},
            ],
        },
        {
            "text": "The DevOps team at an IT company wants to centrally manage servers on AWS Cloud and on-premises to collect software inventory, run commands, configure and patch servers at scale. Which AWS service would you recommend?\n\nĐội DevOps tại một công ty CNTT muốn quản lý tập trung các server trên AWS Cloud cũng như on-premises để thu thập software inventory, chạy lệnh, cấu hình và patch server ở quy mô lớn. Bạn sẽ đề xuất dịch vụ AWS nào?",
            "type": "single",
            "choices": [
                {"text": "AWS Config\nAWS Config", "is_correct": False},
                {"text": "AWS CloudFormation\nAWS CloudFormation", "is_correct": False},
                {"text": "AWS Systems Manager\nAWS Systems Manager", "is_correct": True},
                {"text": "AWS Service Catalog\nAWS Service Catalog", "is_correct": False},
            ],
        },
        {
            "text": "An AWS user is trying to launch an Amazon EC2 instance in a given region. What is the region-specific constraint that the Amazon Machine Image (AMI) must meet?\n\nMột người dùng AWS đang cố gắng launch Amazon EC2 instance trong một region cụ thể. Điều kiện liên quan đến region mà Amazon Machine Image (AMI) phải đáp ứng là gì?",
            "type": "single",
            "choices": [
                {"text": "An AMI is a global entity, so the region is not applicable\nAMI là thực thể toàn cầu nên region không áp dụng", "is_correct": False},
                {"text": "You must use an AMI from the same region as that of the EC2 instance. The region of the AMI has no bearing on the performance of the EC2 instance\nBạn phải sử dụng AMI từ cùng region với EC2 instance. Region của AMI không ảnh hưởng đến hiệu năng của EC2 instance", "is_correct": True},
                {"text": "You can use an AMI from a different region, but it degrades the performance of the EC2 instance\nBạn có thể sử dụng AMI từ region khác nhưng điều đó làm giảm hiệu năng của EC2 instance", "is_correct": False},
                {"text": "You should use an AMI from the same region, as it improves the performance of the EC2 instance\nBạn nên sử dụng AMI từ cùng region vì nó cải thiện hiệu năng của EC2 instance", "is_correct": False},
            ],
        },
    ],
    "Storage Services — S3, EBS, EFS & Glacier": [
        {
            "text": "What is the name for the top-level container used to hold objects within Amazon S3?\n\nTên gọi của vùng chứa cấp cao nhất dùng để lưu trữ các object trong Amazon S3 là gì?",
            "type": "single",
            "choices": [
                {"text": "Directory\nThư mục hệ thống", "is_correct": False},
                {"text": "Bucket\nBucket", "is_correct": True},
                {"text": "Instance Store\nBộ nhớ tạm của EC2 Instance", "is_correct": False},
                {"text": "Folder\nThư mục", "is_correct": False},
            ],
        },
        {
            "text": "Which AWS service can serve a static website?\n\nDịch vụ AWS nào có thể phục vụ một website tĩnh?",
            "type": "single",
            "choices": [
                {"text": "Amazon QuickSight\nAmazon QuickSight", "is_correct": False},
                {"text": "AWS X-Ray\nAWS X-Ray", "is_correct": False},
                {"text": "Amazon Route 53\nAmazon Route 53", "is_correct": False},
                {"text": "Amazon S3\nAmazon S3", "is_correct": True},
            ],
        },
        {
            "text": "Which AWS service can be used to host a static website with the LEAST effort?\n\nDịch vụ AWS nào có thể được sử dụng để host một website tĩnh với ÍT công sức nhất?",
            "type": "single",
            "choices": [
                {"text": "Amazon Elastic File System (Amazon EFS)\nAmazon Elastic File System (Amazon EFS)", "is_correct": False},
                {"text": "Amazon Simple Storage Service (Amazon S3)\nAmazon Simple Storage Service (Amazon S3)", "is_correct": True},
                {"text": "AWS Storage Gateway\nAWS Storage Gateway", "is_correct": False},
                {"text": "Amazon S3 Glacier\nAmazon S3 Glacier", "is_correct": False},
            ],
        },
        {
            "text": "An e-commerce company has on-premises data storage on an NFS file system accessed in parallel by multiple applications. They want to move to AWS with applications hosted on Amazon EC2. Which storage service should they use?\n\nMột công ty thương mại điện tử đang lưu trữ dữ liệu on-premises trên hệ thống file NFS được nhiều ứng dụng truy cập song song. Nếu ứng dụng được host trên Amazon EC2, công ty nên sử dụng dịch vụ lưu trữ nào?",
            "type": "single",
            "choices": [
                {"text": "Amazon Simple Storage Service (Amazon S3)\nAmazon Simple Storage Service (Amazon S3)", "is_correct": False},
                {"text": "AWS Storage Gateway\nAWS Storage Gateway", "is_correct": False},
                {"text": "Amazon Elastic File System (Amazon EFS)\nAmazon Elastic File System (Amazon EFS)", "is_correct": True},
                {"text": "Amazon Elastic Block Store (Amazon EBS)\nAmazon Elastic Block Store (Amazon EBS)", "is_correct": False},
            ],
        },
    ],
    "Databases & Analytics on AWS": [
        {
            "text": "A company is planning to move their traditional CRM application running on MySQL to an AWS database service. Which database service is the right fit?\n\nMột công ty đang có kế hoạch chuyển ứng dụng CRM truyền thống chạy trên MySQL sang dịch vụ cơ sở dữ liệu của AWS. Dịch vụ cơ sở dữ liệu nào phù hợp nhất?",
            "type": "single",
            "choices": [
                {"text": "Amazon DynamoDB\nAmazon DynamoDB", "is_correct": False},
                {"text": "Amazon Neptune\nAmazon Neptune", "is_correct": False},
                {"text": "Amazon ElastiCache\nAmazon ElastiCache", "is_correct": False},
                {"text": "Amazon Aurora\nAmazon Aurora", "is_correct": True},
            ],
        },
        {
            "text": "What is the primary benefit of deploying an Amazon RDS database in a Read Replica configuration?\n\nLợi ích chính của việc triển khai cơ sở dữ liệu Amazon RDS theo cấu hình Read Replica là gì?",
            "type": "single",
            "choices": [
                {"text": "Read Replica improves database scalability\nRead Replica cải thiện khả năng mở rộng của database", "is_correct": True},
                {"text": "Read Replica protects the database from a regional failure\nRead Replica bảo vệ database khỏi lỗi region", "is_correct": False},
                {"text": "Read Replica reduces database usage costs\nRead Replica giảm chi phí sử dụng database", "is_correct": False},
                {"text": "Read Replica enhances database availability\nRead Replica tăng tính sẵn sàng của database", "is_correct": False},
            ],
        },
    ],
    "Networking — VPC, CloudFront & Route 53": [
        {
            "text": "Which of the following acts as a virtual firewall at the Amazon EC2 instance level to control traffic for one or more instances?\n\nThành phần nào sau đây hoạt động như một tường lửa ảo ở cấp độ EC2 instance để kiểm soát traffic cho một hoặc nhiều instance?",
            "type": "single",
            "choices": [
                {"text": "Route table\nBảng định tuyến", "is_correct": False},
                {"text": "Security groups\nSecurity group", "is_correct": True},
                {"text": "Network Access Control Lists (ACL)\nDanh sách kiểm soát truy cập mạng (ACL)", "is_correct": False},
                {"text": "Virtual private gateways (VPG)\nCổng riêng ảo (VPG)", "is_correct": False},
            ],
        },
        {
            "text": "Which of the following will help you control the incoming traffic to an Amazon EC2 instance?\n\nYếu tố nào sau đây sẽ giúp bạn kiểm soát lưu lượng truy cập đi vào một Amazon EC2 instance?",
            "type": "single",
            "choices": [
                {"text": "Network access control list (network ACL)\nDanh sách kiểm soát truy cập mạng (network ACL)", "is_correct": False},
                {"text": "AWS Resource Group\nNhóm tài nguyên AWS", "is_correct": False},
                {"text": "Route Table\nBảng định tuyến", "is_correct": False},
                {"text": "Security Group\nNhóm bảo mật", "is_correct": True},
            ],
        },
        {
            "text": "Which of the following services are provided by Amazon Route 53? (Select Two)\n\nNhững dịch vụ nào sau đây được cung cấp bởi Amazon Route 53? (Chọn HAI đáp án)",
            "type": "multiple",
            "choices": [
                {"text": "Transfer acceleration\nTăng tốc truyền dữ liệu", "is_correct": False},
                {"text": "Load balancing\nCân bằng tải", "is_correct": False},
                {"text": "IP routing\nĐịnh tuyến IP", "is_correct": False},
                {"text": "Domain registration\nĐăng ký tên miền", "is_correct": True},
                {"text": "Health checks and monitoring\nKiểm tra sức khỏe và giám sát", "is_correct": True},
            ],
        },
        {
            "text": "Which of the following statements are correct regarding Amazon API Gateway? (Select two)\n\nNhững phát biểu nào sau đây đúng về Amazon API Gateway? (Chọn HAI đáp án)",
            "type": "multiple",
            "choices": [
                {"text": "If an API response is served by the cached data, it is not considered an API call for billing purposes\nNếu API response được trả từ dữ liệu cache thì sẽ không được tính là API call cho mục đích tính phí", "is_correct": False},
                {"text": "Amazon API Gateway can call an AWS Lambda function to create the front door of a serverless application\nAmazon API Gateway có thể gọi AWS Lambda function để tạo front door cho ứng dụng serverless", "is_correct": True},
                {"text": "Amazon API Gateway does not yet support API result caching\nAmazon API Gateway hiện chưa hỗ trợ cache kết quả API", "is_correct": False},
                {"text": "API Gateway can be configured to send data directly to Amazon Kinesis Data Stream\nAPI Gateway có thể được cấu hình để gửi dữ liệu trực tiếp đến Amazon Kinesis Data Stream", "is_correct": True},
                {"text": "Amazon API Gateway creates RESTful APIs, Storage Gateway creates WebSocket APIs\nAmazon API Gateway tạo RESTful API, còn Storage Gateway tạo WebSocket API", "is_correct": False},
            ],
        },
    ],
    "Security, Compliance & Governance": [
        {
            "text": "Based on the shared responsibility model, which of the following security and compliance tasks is AWS responsible for?\n\nDựa trên mô hình shared responsibility, AWS chịu trách nhiệm cho nhiệm vụ bảo mật và tuân thủ nào sau đây?",
            "type": "single",
            "choices": [
                {"text": "Granting access to individuals and services\nCấp quyền truy cập cho người dùng và dịch vụ", "is_correct": False},
                {"text": "Updating Amazon EC2 host firmware\nCập nhật firmware của host Amazon EC2", "is_correct": True},
                {"text": "Updating operating systems\nCập nhật hệ điều hành", "is_correct": False},
                {"text": "Encrypting data in transit\nMã hóa dữ liệu trong quá trình truyền tải", "is_correct": False},
            ],
        },
        {
            "text": "Which of the following statements are true about AWS Shared Responsibility Model? (Select two)\n\nNhững phát biểu nào sau đây đúng về AWS Shared Responsibility Model? (Chọn HAI đáp án)",
            "type": "multiple",
            "choices": [
                {"text": "AWS maintains the configuration of its infrastructure devices and is responsible for configuring the guest operating systems, databases, and applications\nAWS duy trì cấu hình các thiết bị hạ tầng và chịu trách nhiệm cấu hình guest OS, database và ứng dụng", "is_correct": False},
                {"text": "AWS is responsible for patching and fixing flaws within the infrastructure, but customers are responsible for patching their guest operating system and applications\nAWS chịu trách nhiệm vá lỗi hạ tầng, còn khách hàng chịu trách nhiệm vá lỗi guest OS và ứng dụng", "is_correct": True},
                {"text": "AWS trains AWS employees, but a customer must train their own employees\nAWS đào tạo nhân viên AWS, còn khách hàng phải đào tạo nhân viên của riêng họ", "is_correct": True},
                {"text": "Amazon EC2 is categorized as IaaS and hence AWS will perform all of the necessary security configuration and management tasks\nAmazon EC2 được phân loại là IaaS, do đó AWS sẽ thực hiện tất cả cấu hình và quản lý bảo mật cần thiết", "is_correct": False},
                {"text": "For abstracted services such as Amazon S3, AWS operates the infrastructure layer, the operating system, platforms, encryption options, and appropriate permissions\nĐối với các dịch vụ abstracted như Amazon S3, AWS vận hành lớp hạ tầng, hệ điều hành, nền tảng, tùy chọn mã hóa và quyền truy cập", "is_correct": False},
            ],
        },
        {
            "text": "Which AWS services can be used together to send alerts whenever the AWS account root user signs in? (Select two)\n\nNhững dịch vụ AWS nào có thể được sử dụng cùng nhau để gửi cảnh báo bất cứ khi nào root user của AWS account đăng nhập? (Chọn HAI đáp án)",
            "type": "multiple",
            "choices": [
                {"text": "AWS Lambda\nAWS Lambda", "is_correct": False},
                {"text": "Amazon Simple Queue Service (Amazon SQS)\nAmazon Simple Queue Service (Amazon SQS)", "is_correct": False},
                {"text": "Amazon Simple Notification Service (Amazon SNS)\nAmazon Simple Notification Service (Amazon SNS)", "is_correct": True},
                {"text": "Amazon CloudWatch\nAmazon CloudWatch", "is_correct": True},
                {"text": "AWS Step Functions\nAWS Step Functions", "is_correct": False},
            ],
        },
        {
            "text": "AWS Shield Advanced provides expanded DDoS attack protection for web applications running on which of the following resources? (Select two)\n\nAWS Shield Advanced cung cấp khả năng bảo vệ chống tấn công DDoS nâng cao cho các ứng dụng web chạy trên những tài nguyên nào sau đây? (Chọn HAI đáp án)",
            "type": "multiple",
            "choices": [
                {"text": "Amazon Elastic Compute Cloud (Amazon EC2)\nAmazon Elastic Compute Cloud (Amazon EC2)", "is_correct": True},
                {"text": "Amazon CloudFront\nAmazon CloudFront", "is_correct": True},
                {"text": "Amazon Simple Storage Service (Amazon S3)\nAmazon Simple Storage Service (Amazon S3)", "is_correct": False},
                {"text": "AWS Elastic Beanstalk\nAWS Elastic Beanstalk", "is_correct": False},
                {"text": "AWS Identity and Access Management (AWS IAM)\nAWS Identity and Access Management (AWS IAM)", "is_correct": False},
            ],
        },
        {
            "text": "Which of the following services have data encryption automatically enabled? (Select two)\n\nNhững dịch vụ nào sau đây có mã hóa dữ liệu được bật tự động? (Chọn HAI đáp án)",
            "type": "multiple",
            "choices": [
                {"text": "Amazon Simple Storage Service (Amazon S3)\nAmazon Simple Storage Service (Amazon S3)", "is_correct": True},
                {"text": "Amazon Elastic Block Store (Amazon EBS)\nAmazon Elastic Block Store (Amazon EBS)", "is_correct": False},
                {"text": "AWS Storage Gateway\nAWS Storage Gateway", "is_correct": True},
                {"text": "Amazon Redshift\nAmazon Redshift", "is_correct": False},
                {"text": "Amazon Elastic File System (Amazon EFS)\nAmazon Elastic File System (Amazon EFS)", "is_correct": False},
            ],
        },
    ],
    "Billing, Pricing & AWS Support Plans": [
        {
            "text": "In which ways does AWS' pricing model benefit organizations?\n\nMô hình định giá của AWS mang lại lợi ích cho tổ chức theo cách nào?",
            "type": "single",
            "choices": [
                {"text": "Eliminates licensing costs\nLoại bỏ chi phí bản quyền", "is_correct": False},
                {"text": "Reduce the cost of maintaining idle resources\nGiảm chi phí duy trì tài nguyên nhàn rỗi", "is_correct": True},
                {"text": "Reduces the people cost of application development\nGiảm chi phí nhân sự phát triển ứng dụng", "is_correct": False},
                {"text": "Focus spend on capital expenditure, rather than operational expenditure\nTập trung chi tiêu vào chi phí đầu tư thay vì chi phí vận hành", "is_correct": False},
            ],
        },
        {
            "text": "Bob and Susan each have an AWS account in AWS Organizations. Susan has five Reserved Instances (RIs) of the same type and Bob has none. During one hour, Susan uses three instances and Bob uses six for a total of nine. Which statements are correct about consolidated billing? (Select two)\n\nBob và Susan đều có AWS account trong AWS Organizations. Susan có năm Reserved Instance (RI) cùng loại còn Bob thì không có. Trong một giờ, Susan sử dụng ba instance và Bob sử dụng sáu instance, tổng cộng là chín instance. Những phát biểu nào đúng về consolidated billing? (Chọn HAI đáp án)",
            "type": "multiple",
            "choices": [
                {"text": "Bob does not receive any cost-benefit since he hasn't purchased any Reserved Instance (RI)\nBob không nhận được lợi ích chi phí nào vì anh ấy không mua Reserved Instance (RI)", "is_correct": False},
                {"text": "Bob receives the cost-benefit from Susan's RI only if he launches instances in the same AWS Region where Susan purchased her RIs\nBob chỉ nhận được lợi ích chi phí từ RI của Susan nếu anh ấy launch instance trong cùng AWS Region nơi Susan mua RI", "is_correct": False},
                {"text": "Bob receives the cost-benefit from Susan's RIs only if he launches instances in the same Availability Zone (AZ) where Susan purchased her Reserved Instances\nBob chỉ nhận được lợi ích chi phí từ RI của Susan nếu anh ấy launch instance trong cùng Availability Zone (AZ) nơi Susan mua RI", "is_correct": True},
                {"text": "AWS bills five instances as Reserved Instances, and the remaining four instances as regular instances\nAWS tính phí năm instance theo Reserved Instance và bốn instance còn lại theo giá thông thường", "is_correct": True},
                {"text": "AWS bills three instances as Reserved Instances (RI), and the remaining six instances as regular instances\nAWS tính phí ba instance theo Reserved Instance (RI) và sáu instance còn lại theo giá thông thường", "is_correct": False},
            ],
        },
    ],
}


async def seed_exam_questions(db: AsyncSession) -> int:
    result = await db.execute(select(Subject).where(Subject.name == "AWS Cloud Practitioner"))
    subject = result.scalar_one_or_none()
    if not subject:
        print("  AWS Cloud Practitioner subject not found — run main seed first")
        return 0

    domain_result = await db.execute(select(Domain).where(Domain.subject_id == subject.id))
    all_domains = domain_result.scalars().all()
    domain_map = {d.name: d for d in all_domains}
    domain_ids = [d.id for d in all_domains]

    existing_result = await db.execute(
        select(Question).where(Question.for_exam.is_(True), Question.domain_id.in_(domain_ids))
    )
    existing_questions = existing_result.scalars().all()

    if existing_questions:
        # Build lookup by first 80 chars of English question text
        existing_map = {}
        for q in existing_questions:
            key = q.question_text.split("\n")[0][:80]
            existing_map[key] = q

        updated = 0
        added = 0
        for domain_name, questions in EXAM_QUESTIONS_BY_DOMAIN.items():
            domain = domain_map.get(domain_name)
            if not domain:
                continue
            for q_data in questions:
                key = q_data["text"].split("\n")[0][:80]
                if key in existing_map:
                    eq = existing_map[key]
                    eq.question_text = q_data["text"]
                    eq.choices = [{"text": c["text"], "is_correct": c["is_correct"]} for c in q_data["choices"]]
                    updated += 1
                else:
                    db.add(Question(
                        domain_id=domain.id,
                        source="seed",
                        question_text=q_data["text"],
                        question_type=q_data["type"],
                        choices=[{"text": c["text"], "is_correct": c["is_correct"]} for c in q_data["choices"]],
                        for_exam=True,
                    ))
                    added += 1

        await db.commit()
        print(f"  Updated {updated} questions with bilingual content, added {added} new")
        return updated + added

    # Fresh seed
    count = 0
    for domain_name, questions in EXAM_QUESTIONS_BY_DOMAIN.items():
        domain = domain_map.get(domain_name)
        if not domain:
            print(f"  Domain not found: {domain_name!r}")
            continue
        for q in questions:
            db.add(Question(
                domain_id=domain.id,
                source="seed",
                question_text=q["text"],
                question_type=q["type"],
                choices=[{"text": c["text"], "is_correct": c["is_correct"]} for c in q["choices"]],
                for_exam=True,
            ))
            count += 1

    await db.commit()
    return count
