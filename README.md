# Hotmart Facebook Campaign System Documentation

## Table of Contents
- [Overview](#overview)
- [Setup Requirements](#setup-requirements)
- [Product Configuration](#product-configuration)
  - [HotmartProduct Parameters](#hotmartproduct-parameters)
  - [Product Examples](#product-examples)
- [Facebook Campaign Configuration](#facebook-campaign-configuration)
  - [Campaign Parameters](#campaign-parameters)
  - [Audience Targeting](#audience-targeting)
  - [Ad Sets](#ad-sets)
  - [Ad Creatives](#ad-creatives)
  - [Campaign Rules](#campaign-rules)
- [Best Practices](#best-practices)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Overview

This system enables automated creation and management of Facebook ad campaigns for Hotmart products. It consists of two main components:
- Product configuration (`HotmartProduct`)
- Campaign configuration (`FacebookCampaignParameters`)

## Setup Requirements

```python
# Required environment variables
FB_ACCESS_TOKEN="your_facebook_access_token"
FB_AD_ACCOUNT_ID="your_ad_account_id"
FB_PIXEL_ID="your_pixel_id"
CLAUDE_API_KEY="your_claude_api_key"
```

## Product Configuration

### HotmartProduct Parameters

#### 1. Basic Information
```python
name: str  # Product name
base_url: str  # Hotmart product base URL
affiliate_id: str  # Your Hotmart affiliate ID
price: float  # Product price
description: str  # Product description
```

**Example:**
```python
name="Digital Marketing Course 2024"
base_url="https://go.hotmart.com/M97671048E"
affiliate_id="M97671048E"
price=197.0
description="Complete digital marketing course with practical projects"
```

#### 2. Target Audience Configuration
```python
target_audience: Dict[str, List[str]]
```

**Structure:**
```python
target_audience={
    'interests': [...],  # Interest-based targeting
    'keywords': [...],   # Search keywords
    'demographics': [...] # Demographic groups
}
```

**Example:**
```python
target_audience={
    'interests': ['digital marketing', 'online business', 'entrepreneurship'],
    'keywords': ['learn marketing', 'digital skills', 'online course'],
    'demographics': ['professionals', 'business owners', 'students']
}
```

#### 3. Media Assets
```python
images: List[str]  # List of image URLs
videos: Optional[List[str]]  # List of video URLs
```

**Best Practices:**
- Images: 1200x628px for feed ads
- Square images: 1080x1080px for Instagram
- Videos: 16:9 aspect ratio, 720p minimum
- Keep videos under 2 minutes

**Example:**
```python
images=[
    'https://path.to/main-banner.jpg',
    'https://path.to/square-banner.jpg'
]
videos=[
    'https://path.to/product-demo.mp4',
    'https://path.to/testimonial-video.mp4'
]
```

## Facebook Campaign Configuration

### Campaign Parameters

#### 1. Basic Campaign Settings
```python
name: str  # Campaign name
objective: CampaignObjective  # Campaign objective
buying_type: str = 'AUCTION'  # Campaign buying type
status: str = 'PAUSED'  # Initial campaign status
daily_budget: float  # Daily budget in your currency
```

**Objectives Available:**
```python
CampaignObjective = {
    'OUTCOME_SALES',      # For direct sales
    'OUTCOME_LEADS',      # For lead generation
    'OUTCOME_AWARENESS',  # For brand awareness
    'OUTCOME_TRAFFIC',    # For website traffic
    'OUTCOME_ENGAGEMENT'  # For post engagement
}
```

**Example:**
```python
campaign_params = FacebookCampaignParameters(
    name="Digital Marketing Course Launch",
    objective=CampaignObjective.OUTCOME_SALES,
    daily_budget=50.0,
    bid_strategy=BidStrategy.LOWEST_COST_WITH_BID_CAP
)
```

### Audience Targeting

#### 1. Cold Audience
```python
cold_audience=AudienceTargeting(
    age_range=(25, 55),
    genders=[1, 2],  # 1=male, 2=female
    languages=['EN'],
    locations=['US', 'CA', 'UK', 'AU'],
    interests=['digital marketing', 'online business']
)
```

#### 2. Warm Audience
```python
warm_audience=AudienceTargeting(
    age_range=(25, 55),
    genders=[1, 2],
    languages=['EN'],
    locations=['US', 'CA', 'UK', 'AU'],
    custom_audiences=['WEBSITE_VISITORS_30D']
)
```

#### 3. Hot Audience
```python
hot_audience=AudienceTargeting(
    age_range=(25, 55),
    genders=[1, 2],
    languages=['EN'],
    locations=['US', 'CA', 'UK', 'AU'],
    custom_audiences=['CART_ABANDONERS_7D']
)
```

### Ad Sets

Each ad set represents a specific targeting group and budget allocation.

```python
AdSetParameters(
    name: str,  # Ad set name
    optimization_goal: OptimizationGoal,  # Optimization objective
    billing_event: str,  # How you're charged
    bid_strategy: BidStrategy,  # Bidding strategy
    targeting: AudienceTargeting,  # Targeting settings
    daily_budget: float,  # Daily budget for this ad set
    placements: List[Placement]  # Ad placements
)
```

**Optimization Goals:**
```python
OptimizationGoal = {
    'REACH',              # Maximum reach
    'IMPRESSIONS',        # Maximum impressions
    'LINK_CLICKS',        # Link clicks
    'LANDING_PAGE_VIEWS', # Landing page views
    'VALUE'              # Return on ad spend
}
```

**Example:**
```python
ad_sets=[
    AdSetParameters(
        name="Cold Traffic - Interest Based",
        optimization_goal=OptimizationGoal.REACH,
        billing_event='IMPRESSIONS',
        bid_strategy=BidStrategy.LOWEST_COST_WITHOUT_CAP,
        daily_budget=20.0,
        targeting=cold_audience,
        placements=[
            Placement(
                platform='facebook',
                position='feed',
                device_types=['mobile', 'desktop']
            )
        ]
    )
]
```

### Ad Creatives

Define the actual ad content for each variation:

```python
AdCreative(
    primary_text: str,    # Main ad text
    headline: str,        # Ad headline
    description: str,     # Additional description
    call_to_action: str,  # CTA button text
    link_destination: str # Landing page type
)
```

**Best Practices for Ad Copy:**
- Primary Text: 125-250 characters
- Headline: 25-40 characters
- Description: 20-30 characters

**Example:**
```python
ad_creatives=[
    AdCreative(
        primary_text="Master Digital Marketing with our comprehensive course. Learn practical skills you can apply immediately.",
        headline="Transform Your Marketing Skills",
        description="Limited Time Offer",
        call_to_action="LEARN_MORE",
        link_destination="sales"
    )
]
```

### Campaign Rules

Define automation rules for campaign optimization:

```python
campaign_rules={
    'budget_optimization': bool,
    'scheduling': Dict,
    'budget_rules': Dict
}
```

**Example:**
```python
campaign_rules={
    'budget_optimization': True,
    'scheduling': {
        'start_time': '2024-01-21T00:00:00+0000',
        'end_time': '2024-02-21T00:00:00+0000'
    },
    'budget_rules': {
        'min_roas': 2.0,
        'max_cost_per_result': 50.0,
        'daily_budget_adjustment': {
            'increase_threshold': 3.0,
            'decrease_threshold': 1.5,
            'adjustment_percentage': 0.15
        }
    }
}
```

## Best Practices

1. Budget Allocation:
   - Cold audience: 70% of budget
   - Warm audience: 20% of budget
   - Hot audience: 10% of budget

2. Targeting Strategy:
   - Start broad with cold audiences
   - Use custom audiences for warm/hot
   - Test different interest combinations

3. Ad Creative:
   - Test multiple images/videos
   - Use clear call-to-actions
   - Include social proof
   - Keep copy concise and compelling

4. Optimization:
   - Start with higher budgets for learning
   - Optimize based on ROAS
   - Test different placements
   - Monitor frequency caps

## Examples

### Complete Campaign Setup Example

```python
from dotenv import load_dotenv
load_dotenv()

# Product Configuration
product = HotmartProduct(
    name="Digital Marketing Mastery",
    base_url="https://go.hotmart.com/M97671048E",
    affiliate_id="M97671048E",
    price=197.0,
    description="Complete A-Z Digital Marketing Course",
    target_audience={
        'interests': ['digital marketing', 'online business'],
        'keywords': ['learn marketing', 'digital skills'],
        'demographics': ['professionals', 'students']
    },
    images=['https://path.to/image1.jpg'],
    videos=['https://path.to/video1.mp4']
)

# Campaign Configuration
campaign_params = FacebookCampaignParameters(
    name="Digital Marketing Course Launch",
    objective=CampaignObjective.OUTCOME_SALES,
    daily_budget=50.0,
    bid_strategy=BidStrategy.LOWEST_COST_WITH_BID_CAP,
    # ... (other parameters as shown above)
)

# Create Campaign
fb_manager = FacebookCampaignManager(
    access_token=os.getenv('FB_ACCESS_TOKEN'),
    ad_account_id=os.getenv('FB_AD_ACCOUNT_ID'),
    claude_api_key=os.getenv('CLAUDE_API_KEY')
)

campaign = fb_manager.create_campaign(product, campaign_params)
```

## Troubleshooting

1. Common Issues:
   - Media upload failures
   - Targeting restrictions
   - Budget limitations
   - Ad disapprovals

2. Solutions:
   - Verify media specifications
   - Check targeting compliance
   - Monitor budget settings
   - Review ad policies

