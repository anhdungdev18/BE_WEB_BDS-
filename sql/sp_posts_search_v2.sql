-- Update search/count procedures to support include_all (admin) behavior.
-- Call with p_include_all=1 for admin; 0 for public.

DELIMITER $$

DROP PROCEDURE IF EXISTS sp_posts_search$$
CREATE PROCEDURE sp_posts_search(
    IN p_q            VARCHAR(255),
    IN p_category_id  INT,
    IN p_post_type_id INT,
    IN p_price_min    DECIMAL(15,2),
    IN p_price_max    DECIMAL(15,2),
    IN p_area_min     DOUBLE,
    IN p_area_max     DOUBLE,
    IN p_province     VARCHAR(100),
    IN p_district     VARCHAR(100),
    IN p_ward         VARCHAR(100),
    IN p_sort         VARCHAR(32),
    IN p_order        VARCHAR(4),
    IN p_page         INT,
    IN p_page_size    INT,
    IN p_include_all  TINYINT
)
BEGIN
    DECLARE v_page   INT DEFAULT IFNULL(p_page, 1);
    DECLARE v_size   INT DEFAULT IFNULL(p_page_size, 20);
    DECLARE v_offset INT DEFAULT (v_page - 1) * v_size;

    DECLARE v_sort_col VARCHAR(32) DEFAULT IFNULL(p_sort, 'created_at');
    DECLARE v_order    VARCHAR(4)  DEFAULT IFNULL(p_order, 'desc');
    DECLARE v_include_all TINYINT DEFAULT IFNULL(p_include_all, 0);

    SELECT
      JSON_OBJECT(
        'id',             p.id,
        'title',          p.title,
        'price',          p.price,
        'area',           p.area,
        'category_id',    p.category_id,
        'post_type_id',   p.post_type_id,
        'created_at',     p.created_at,
        'post_status',    ps.name,
        'approval_status',aps.name,
        'owner_is_agent', p.owner_is_agent,
        'bumped_at',      p.bumped_at
      ) AS result
    FROM listings_post p
    LEFT JOIN listings_poststatus ps      ON ps.id = p.post_status_id
    LEFT JOIN listings_approvalstatus aps ON aps.id = p.approval_status_id
    WHERE p.is_deleted = 0
      AND (v_include_all = 1 OR (aps.name = 'Approved' AND ps.name = 'Published'))
      AND (p_q IS NULL OR p_q = '' OR p.title LIKE CONCAT('%', p_q, '%')
           OR p.description LIKE CONCAT('%', p_q, '%'))
      AND (p_category_id  IS NULL OR p.category_id  = p_category_id)
      AND (p_post_type_id IS NULL OR p.post_type_id = p_post_type_id)
      AND (p_price_min IS NULL OR p.price >= p_price_min)
      AND (p_price_max IS NULL OR p.price <= p_price_max)
      AND (p_area_min  IS NULL OR p.area  >= p_area_min)
      AND (p_area_max  IS NULL OR p.area  <= p_area_max)
      AND (p_province IS NULL OR JSON_EXTRACT(p.address,'$.province') = p_province)
      AND (p_district IS NULL OR JSON_EXTRACT(p.address,'$.district') = p_district)
      AND (p_ward     IS NULL OR JSON_EXTRACT(p.address,'$.ward')     = p_ward)
    ORDER BY
      p.owner_is_agent DESC,
      p.bumped_at DESC,
      CASE WHEN (v_sort_col='created_at' AND LOWER(v_order)='asc')  THEN p.created_at END ASC,
      CASE WHEN (v_sort_col='created_at' AND LOWER(v_order)='desc') THEN p.created_at END DESC,
      CASE WHEN (v_sort_col='price'      AND LOWER(v_order)='asc')  THEN p.price END ASC,
      CASE WHEN (v_sort_col='price'      AND LOWER(v_order)='desc') THEN p.price END DESC,
      CASE WHEN (v_sort_col='area'       AND LOWER(v_order)='asc')  THEN p.area END ASC,
      CASE WHEN (v_sort_col='area'       AND LOWER(v_order)='desc') THEN p.area END DESC,
      p.created_at DESC
    LIMIT v_size OFFSET v_offset;
END$$

DROP PROCEDURE IF EXISTS sp_posts_count$$
CREATE PROCEDURE sp_posts_count(
    IN p_q            VARCHAR(255),
    IN p_category_id  INT,
    IN p_post_type_id INT,
    IN p_price_min    DECIMAL(15,2),
    IN p_price_max    DECIMAL(15,2),
    IN p_area_min     DOUBLE,
    IN p_area_max     DOUBLE,
    IN p_province     VARCHAR(100),
    IN p_district     VARCHAR(100),
    IN p_ward         VARCHAR(100),
    IN p_include_all  TINYINT
)
BEGIN
    DECLARE v_include_all TINYINT DEFAULT IFNULL(p_include_all, 0);

    SELECT JSON_OBJECT('total', COUNT(*)) AS result
    FROM listings_post p
    LEFT JOIN listings_poststatus ps      ON ps.id = p.post_status_id
    LEFT JOIN listings_approvalstatus aps ON aps.id = p.approval_status_id
    WHERE p.is_deleted = 0
      AND (v_include_all = 1 OR (aps.name = 'Approved' AND ps.name = 'Published'))
      AND (p_q IS NULL OR p_q = '' OR p.title LIKE CONCAT('%', p_q, '%')
           OR p.description LIKE CONCAT('%', p_q, '%'))
      AND (p_category_id  IS NULL OR p.category_id  = p_category_id)
      AND (p_post_type_id IS NULL OR p.post_type_id = p_post_type_id)
      AND (p_price_min IS NULL OR p.price >= p_price_min)
      AND (p_price_max IS NULL OR p.price <= p_price_max)
      AND (p_area_min  IS NULL OR p.area  >= p_area_min)
      AND (p_area_max  IS NULL OR p.area  <= p_area_max)
      AND (p_province IS NULL OR JSON_EXTRACT(p.address,'$.province') = p_province)
      AND (p_district IS NULL OR JSON_EXTRACT(p.address,'$.district') = p_district)
      AND (p_ward     IS NULL OR JSON_EXTRACT(p.address,'$.ward')     = p_ward);
END$$

DELIMITER ;
