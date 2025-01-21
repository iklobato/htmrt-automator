from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
import os
from datetime import datetime, timedelta
import requests
import anthropic
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adimage import AdImage
from facebook_business.adobjects.advideo import AdVideo


class CampaignObjective(str, Enum):
    OUTCOME_SALES = 'OUTCOME_SALES'
    OUTCOME_LEADS = 'OUTCOME_LEADS'
    OUTCOME_AWARENESS = 'OUTCOME_AWARENESS'
    OUTCOME_TRAFFIC = 'OUTCOME_TRAFFIC'
    OUTCOME_ENGAGEMENT = 'OUTCOME_ENGAGEMENT'
    REACH = 'REACH'


class OptimizationGoal(str, Enum):
    REACH = 'REACH'
    IMPRESSIONS = 'IMPRESSIONS'
    LINK_CLICKS = 'LINK_CLICKS'
    LANDING_PAGE_VIEWS = 'LANDING_PAGE_VIEWS'
    VALUE = 'VALUE'


class BidStrategy(str, Enum):
    LOWEST_COST_WITHOUT_CAP = 'LOWEST_COST_WITHOUT_CAP'
    LOWEST_COST_WITH_BID_CAP = 'LOWEST_COST_WITH_BID_CAP'
    COST_CAP = 'COST_CAP'


@dataclass
class Placement:
    platform: str
    position: str
    device_types: List[str]
    enabled: bool = True


@dataclass
class AudienceTargeting:
    age_range: tuple = (18, 65)
    genders: List[int] = None
    languages: List[str] = None
    locations: List[str] = None
    interests: List[str] = None
    behaviors: List[str] = None
    demographics: List[str] = None
    excluded_interests: List[str] = None
    custom_audiences: List[str] = None
    lookalike_audiences: List[str] = None
    excluded_custom_audiences: List[str] = None


@dataclass
class AdCreative:
    primary_text: str
    headline: str
    description: str
    call_to_action: str
    image_hash: Optional[str] = None
    video_id: Optional[str] = None
    link_destination: Optional[str] = None
    display_link: Optional[str] = None


@dataclass
class AdSetParameters:
    name: str
    optimization_goal: OptimizationGoal
    billing_event: str
    bid_strategy: BidStrategy
    targeting: AudienceTargeting
    daily_budget: float
    lifetime_budget: Optional[float] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    schedule: Optional[List[Dict]] = None
    placements: List[Placement] = None


@dataclass
class FacebookCampaignParameters:
    name: str
    objective: CampaignObjective
    buying_type: str = 'AUCTION'
    status: str = 'PAUSED'
    daily_budget: float = 10.0
    bid_strategy: BidStrategy = BidStrategy.LOWEST_COST_WITHOUT_CAP
    cold_audience: AudienceTargeting = None
    warm_audience: AudienceTargeting = None
    hot_audience: AudienceTargeting = None
    placements: List[Placement] = None
    conversion_tracking: Dict[str, str] = None
    pixel_id: str = None
    ad_sets: List[AdSetParameters] = None
    ad_creatives: List[AdCreative] = None
    special_ad_categories: List[str] = None
    campaign_rules: Optional[Dict] = None


@dataclass
class HotmartProduct:
    name: str
    base_url: str
    affiliate_id: str
    price: float
    description: str
    target_audience: Dict[str, List[str]]
    images: List[str]
    videos: Optional[List[str]] = None
    testimonials: Optional[List[Dict]] = None

    def __post_init__(self):
        self.urls = {
            'sales': self.base_url,
            'product': f"{self.base_url}?dp=1",
            'checkout': f"{self.base_url}?ap=838e",
            'order_bump': f"{self.base_url}?ap=25f0",
        }


class MediaManager:
    def __init__(self, ad_account):
        self.ad_account = ad_account
        self.uploaded_media = {}

    def upload_media(self, media_urls: Dict[str, List[str]]) -> Dict[str, List[str]]:
        media_ids = {'images': [], 'videos': []}

        if media_urls.get('images'):
            for image_url in media_urls['images']:
                image_id = self._upload_image(image_url)
                if image_id:
                    media_ids['images'].append(image_id)

        if media_urls.get('videos'):
            for video_url in media_urls['videos']:
                video_id = self._upload_video(video_url)
                if video_id:
                    media_ids['videos'].append(video_id)

        return media_ids

    def _upload_image(self, image_url: str) -> Optional[str]:
        try:
            response = requests.get(image_url)
            image_hash = AdImage(parent_id=self.ad_account.get_id()).remote_create(
                params={'bytes': response.content}
            )
            return image_hash['hash']
        except Exception as e:
            print(f"Error uploading image {image_url}: {e}")
            return None

    def _upload_video(self, video_url: str) -> Optional[str]:
        try:
            video = AdVideo(parent_id=self.ad_account.get_id()).remote_create(
                params={'file_url': video_url}
            )
            return video['id']
        except Exception as e:
            print(f"Error uploading video {video_url}: {e}")
            return None


class FacebookCampaignManager:
    def __init__(self, access_token: str, ad_account_id: str, claude_api_key: str):
        self.claude = anthropic.Anthropic(api_key=claude_api_key)
        FacebookAdsApi.init(access_token=access_token)
        self.ad_account = AdAccount(ad_account_id)
        self.media_manager = MediaManager(self.ad_account)

    def create_campaign(
        self, product: HotmartProduct, campaign_params: FacebookCampaignParameters
    ):
        media_ids = self.media_manager.upload_media(
            {
                'images': product.images,
                'videos': product.videos if product.videos else [],
            }
        )

        campaign = self._create_base_campaign(product, campaign_params)

        for ad_set_params in campaign_params.ad_sets:
            adset = self._create_adset(campaign, ad_set_params, product)
            self._create_ads(adset, campaign_params.ad_creatives, product, media_ids)

        return campaign

    def _create_base_campaign(
        self, product: HotmartProduct, params: FacebookCampaignParameters
    ):
        return self.ad_account.create_campaign(
            params={
                'name': f"{params.name}_{datetime.now().strftime('%Y%m%d')}",
                'objective': params.objective.value,
                'status': params.status,
                'special_ad_categories': params.special_ad_categories or [],
                'daily_budget': params.daily_budget * 100,
                'bid_strategy': params.bid_strategy.value,
                'buying_type': params.buying_type,
            }
        )

    def _create_adset(self, campaign, params: AdSetParameters, product: HotmartProduct):
        return AdSet(parent_id=campaign.get_id()).create(
            params={
                'name': params.name,
                'campaign_id': campaign.get_id(),
                'daily_budget': params.daily_budget * 100,
                'optimization_goal': params.optimization_goal.value,
                'billing_event': params.billing_event,
                'bid_strategy': params.bid_strategy.value,
                'targeting': self._build_targeting_spec(params.targeting),
                'start_time': params.start_time,
                'end_time': params.end_time,
                'status': 'PAUSED',
            }
        )

    def _build_targeting_spec(self, targeting: AudienceTargeting) -> dict:
        spec = {
            'age_min': targeting.age_range[0],
            'age_max': targeting.age_range[1],
            'genders': targeting.genders,
            'geo_locations': {'countries': targeting.locations},
        }

        if targeting.interests:
            spec['interests'] = [{'id': interest} for interest in targeting.interests]

        if targeting.behaviors:
            spec['behaviors'] = [{'id': behavior} for behavior in targeting.behaviors]

        if targeting.custom_audiences:
            spec['custom_audiences'] = [
                {'id': audience} for audience in targeting.custom_audiences
            ]

        if targeting.excluded_custom_audiences:
            spec['excluded_custom_audiences'] = [
                {'id': audience} for audience in targeting.excluded_custom_audiences
            ]

        return spec

    def _create_ads(
        self,
        adset,
        creatives: List[AdCreative],
        product: HotmartProduct,
        media_ids: Dict[str, List[str]],
    ):
        for creative in creatives:
            for image_hash in media_ids['images']:
                self._create_image_ad(adset, creative, product, image_hash)

            for video_id in media_ids['videos']:
                self._create_video_ad(adset, creative, product, video_id)

    def _create_image_ad(
        self, adset, creative: AdCreative, product: HotmartProduct, image_hash: str
    ):
        ad_creative = self.ad_account.create_ad_creative(
            params={
                'name': f'Creative_{datetime.now().strftime("%Y%m%d")}',
                'object_story_spec': {
                    'page_id': os.getenv('FB_PAGE_ID'),
                    'link_data': {
                        'link': creative.link_destination or product.urls['sales'],
                        'message': creative.primary_text,
                        'headline': creative.headline,
                        'description': creative.description,
                        'image_hash': image_hash,
                        'call_to_action': {'type': creative.call_to_action},
                    },
                },
            }
        )

        Ad(parent_id=adset.get_id()).create(
            params={
                'name': f'Ad_Image_{datetime.now().strftime("%Y%m%d")}',
                'adset_id': adset.get_id(),
                'creative': {'creative_id': ad_creative.get_id()},
                'status': 'PAUSED',
            }
        )

    def _create_video_ad(
        self, adset, creative: AdCreative, product: HotmartProduct, video_id: str
    ):
        ad_creative = self.ad_account.create_ad_creative(
            params={
                'name': f'Creative_Video_{datetime.now().strftime("%Y%m%d")}',
                'object_story_spec': {
                    'page_id': os.getenv('FB_PAGE_ID'),
                    'video_data': {
                        'video_id': video_id,
                        'call_to_action': {'type': creative.call_to_action},
                        'image_url': creative.thumbnail_url,
                        'title': creative.headline,
                        'message': creative.primary_text,
                        'description': creative.description,
                        'link_description': creative.description,
                    },
                },
            }
        )

        Ad(parent_id=adset.get_id()).create(
            params={
                'name': f'Ad_Video_{datetime.now().strftime("%Y%m%d")}',
                'adset_id': adset.get_id(),
                'creative': {'creative_id': ad_creative.get_id()},
                'status': 'PAUSED',
            }
        )


if __name__ == '__main__':
    from dotenv import load_dotenv

    load_dotenv()

    product = HotmartProduct(
        name="Digital Marketing Mastery",
        base_url="https://go.hotmart.com/M97671048E",
        affiliate_id="M97671048E",
        price=197.0,
        description="Complete A-Z Digital Marketing Course with Practical Projects",
        target_audience={
            'interests': ['digital marketing', 'online business', 'entrepreneurship'],
            'keywords': [
                'learn digital marketing',
                'marketing course',
                'online marketing',
            ],
            'demographics': ['professionals', 'business owners', 'students'],
        },
        images=['https://path.to/image1.jpg', 'https://path.to/image2.jpg'],
        videos=['https://path.to/video1.mp4'],
    )

    campaign_params = FacebookCampaignParameters(
        name="Hotmart Digital Marketing Course",
        objective=CampaignObjective.OUTCOME_SALES,
        daily_budget=50.0,
        bid_strategy=BidStrategy.LOWEST_COST_WITH_BID_CAP,
        pixel_id=os.getenv('FB_PIXEL_ID'),
        cold_audience=AudienceTargeting(
            age_range=(25, 55),
            genders=[1, 2],
            languages=['EN'],
            locations=['US', 'CA', 'UK', 'AU'],
            interests=['digital marketing', 'online business', 'entrepreneurship'],
        ),
        warm_audience=AudienceTargeting(
            age_range=(25, 55),
            genders=[1, 2],
            languages=['EN'],
            locations=['US', 'CA', 'UK', 'AU'],
            custom_audiences=[os.getenv('WEBSITE_VISITORS_AUDIENCE_ID')],
        ),
        hot_audience=AudienceTargeting(
            age_range=(25, 55),
            genders=[1, 2],
            languages=['EN'],
            locations=['US', 'CA', 'UK', 'AU'],
            custom_audiences=[os.getenv('CART_ABANDONERS_AUDIENCE_ID')],
        ),
        ad_sets=[
            AdSetParameters(
                name="Cold Traffic - Interests",
                optimization_goal=OptimizationGoal.REACH,
                billing_event='IMPRESSIONS',
                bid_strategy=BidStrategy.LOWEST_COST_WITHOUT_CAP,
                daily_budget=20.0,
                targeting=AudienceTargeting(
                    age_range=(25, 55),
                    interests=['digital marketing', 'online business'],
                ),
                placements=[
                    Placement(
                        platform='facebook',
                        position='feed',
                        device_types=['mobile', 'desktop'],
                    ),
                    Placement(
                        platform='instagram', position='feed', device_types=['mobile']
                    ),
                ],
            ),
            AdSetParameters(
                name="Warm Traffic - Website Visitors",
                optimization_goal=OptimizationGoal.LINK_CLICKS,
                billing_event='IMPRESSIONS',
                bid_strategy=BidStrategy.LOWEST_COST_WITH_BID_CAP,
                daily_budget=15.0,
                targeting=AudienceTargeting(
                    custom_audiences=[os.getenv('WEBSITE_VISITORS_AUDIENCE_ID')],
                    age_range=(25, 55),
                    locations=['US', 'CA', 'UK', 'AU'],
                ),
                placements=[
                    Placement(
                        platform='facebook',
                        position='feed',
                        device_types=['mobile', 'desktop'],
                    ),
                    Placement(
                        platform='facebook',
                        position='right_hand_column',
                        device_types=['desktop'],
                    ),
                ],
            ),
            AdSetParameters(
                name="Hot Traffic - Cart Abandoners",
                optimization_goal=OptimizationGoal.VALUE,
                billing_event='IMPRESSIONS',
                bid_strategy=BidStrategy.LOWEST_COST_WITH_BID_CAP,
                daily_budget=15.0,
                targeting=AudienceTargeting(
                    custom_audiences=[os.getenv('CART_ABANDONERS_AUDIENCE_ID')],
                    age_range=(25, 55),
                    locations=['US', 'CA', 'UK', 'AU'],
                ),
                placements=[
                    Placement(
                        platform='facebook',
                        position='feed',
                        device_types=['mobile', 'desktop'],
                    )
                ],
            ),
        ],
        ad_creatives=[
            AdCreative(
                primary_text="Master Digital Marketing with hands-on experience. Join our comprehensive course designed for beginners and intermediates alike. Learn from industry experts and get practical skills you can apply immediately.",
                headline="Master Digital Marketing Skills",
                description="Complete A-Z Course Available Now",
                call_to_action="LEARN_MORE",
                link_destination="sales",
            ),
            AdCreative(
                primary_text="Ready to transform your business? Our proven digital marketing strategies have helped thousands of students achieve their goals. Start your journey to mastery today.",
                headline="Transform Your Marketing Skills",
                description="Join Successful Students Now",
                call_to_action="SIGN_UP",
                link_destination="product",
            ),
            AdCreative(
                primary_text="Last chance to join our comprehensive digital marketing course. Limited time offer available now. Don't miss out on mastering the skills that can transform your career.",
                headline="Limited Time Offer - Join Now",
                description="Exclusive Access Available",
                call_to_action="GET_OFFER",
                link_destination="checkout",
            ),
        ],
        conversion_tracking={
            'pixel_id': os.getenv('FB_PIXEL_ID'),
            'custom_events': [
                'Purchase',
                'InitiateCheckout',
                'ViewContent',
                'AddToCart',
                'Lead',
            ],
        },
        campaign_rules={
            'budget_optimization': True,
            'scheduling': {
                'start_time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S+0000'),
                'end_time': (datetime.now() + timedelta(days=30)).strftime(
                    '%Y-%m-%dT%H:%M:%S+0000'
                ),
            },
            'budget_rules': {
                'min_roas': 2.0,
                'max_cost_per_result': 50.0,
                'daily_budget_adjustment': {
                    'increase_threshold': 3.0,  # ROAS threshold for budget increase
                    'decrease_threshold': 1.5,  # ROAS threshold for budget decrease
                    'adjustment_percentage': 0.15,  # 15% adjustment up or down
                },
            },
        },
    )

    fb_manager = FacebookCampaignManager(
        access_token=os.getenv('FB_ACCESS_TOKEN'),
        ad_account_id=os.getenv('FB_AD_ACCOUNT_ID'),
        claude_api_key=os.getenv('CLAUDE_API_KEY'),
    )

    campaign = fb_manager.create_campaign(product, campaign_params)
    print(f"Campaign created successfully with ID: {campaign.get_id()}")

